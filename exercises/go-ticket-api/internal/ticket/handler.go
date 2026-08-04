package ticket

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
)

type Handler struct {
	service *Service
	logger  *slog.Logger
}

type response struct {
	Code      string `json:"code"`
	Message   string `json:"message"`
	RequestID string `json:"request_id"`
	Data      any    `json:"data"`
}

func NewHandler(service *Service, logger *slog.Logger) *Handler {
	return &Handler{service: service, logger: logger}
}

func (h *Handler) Register(mux *http.ServeMux) {
	mux.HandleFunc("POST /api/v1/tickets", h.create)
	mux.HandleFunc("GET /api/v1/tickets", h.list)
	mux.HandleFunc("GET /api/v1/tickets/{id}", h.get)
	mux.HandleFunc("POST /api/v1/tickets/{id}/close", h.close)
}

func (h *Handler) create(w http.ResponseWriter, r *http.Request) {
	principal, err := principalFromContext(r.Context())
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	var input CreateInput
	if code, ok := decodeStrictJSON(w, r, &input); !ok {
		status := http.StatusBadRequest
		if code == "invalid_ticket_input" {
			status = http.StatusUnprocessableEntity
		}
		writeError(w, r, status, code, "invalid request body")
		return
	}

	value, err := h.service.Create(r.Context(), principal.TenantID, input)
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	h.logger.Info("ticket created", "ticket_id", value.ID, "request_id", requestID(r))
	writeJSON(w, http.StatusCreated, response{
		Code: "ok", Message: "created", RequestID: requestID(r), Data: value,
	})
}

func (h *Handler) get(w http.ResponseWriter, r *http.Request) {
	principal, err := principalFromContext(r.Context())
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	value, err := h.service.Get(r.Context(), r.PathValue("id"), principal.TenantID)
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, response{
		Code: "ok", Message: "ok", RequestID: requestID(r), Data: value,
	})
}

func (h *Handler) list(w http.ResponseWriter, r *http.Request) {
	principal, err := principalFromContext(r.Context())
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	limit := 20
	if raw := r.URL.Query().Get("limit"); raw != "" {
		limit, err = strconv.Atoi(raw)
		if err != nil {
			writeError(w, r, http.StatusUnprocessableEntity, "invalid_ticket_input", "invalid limit")
			return
		}
	}
	values, err := h.service.List(r.Context(), principal.TenantID, limit)
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, response{
		Code: "ok", Message: "ok", RequestID: requestID(r), Data: values,
	})
}

func (h *Handler) close(w http.ResponseWriter, r *http.Request) {
	principal, err := principalFromContext(r.Context())
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	var input CloseInput
	if code, ok := decodeStrictJSON(w, r, &input); !ok {
		status := http.StatusBadRequest
		if code == "invalid_ticket_input" {
			status = http.StatusUnprocessableEntity
		}
		writeError(w, r, status, code, "invalid request body")
		return
	}
	value, err := h.service.Close(
		r.Context(),
		r.PathValue("id"),
		principal.TenantID,
		input.ExpectedVersion,
	)
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, response{
		Code: "ok", Message: "ok", RequestID: requestID(r), Data: value,
	})
}

func (h *Handler) handleError(w http.ResponseWriter, r *http.Request, err error) {
	switch {
	case errors.Is(err, ErrAuthentication):
		writeError(w, r, http.StatusUnauthorized, "authentication_required", err.Error())
	case errors.Is(err, ErrInvalidInput):
		writeError(w, r, http.StatusUnprocessableEntity, "invalid_ticket_input", err.Error())
	case errors.Is(err, ErrNotFound):
		writeError(w, r, http.StatusNotFound, "ticket_not_found", err.Error())
	case errors.Is(err, ErrStateConflict):
		writeError(w, r, http.StatusConflict, "ticket_state_conflict", err.Error())
	case errors.Is(err, ErrVersionConflict):
		writeError(w, r, http.StatusConflict, "ticket_version_conflict", err.Error())
	default:
		h.logger.Error("request failed", "error", err, "request_id", requestID(r))
		writeError(w, r, http.StatusInternalServerError, "internal_error", "internal error")
	}
}

func decodeStrictJSON(w http.ResponseWriter, r *http.Request, target any) (string, bool) {
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		if strings.Contains(err.Error(), "unknown field") {
			return "invalid_ticket_input", false
		}
		return "invalid_json", false
	}
	if err := decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		return "invalid_json", false
	}
	return "", true
}

func RequestContext(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := strings.TrimSpace(r.Header.Get("X-Request-ID"))
		if id == "" {
			generated, err := newID()
			if err != nil {
				http.Error(w, "cannot create request id", http.StatusInternalServerError)
				return
			}
			id = "req_" + generated
		}
		r.Header.Set("X-Request-ID", id)
		w.Header().Set("X-Request-ID", id)
		next.ServeHTTP(w, r)
	})
}

func requestID(r *http.Request) string {
	return r.Header.Get("X-Request-ID")
}

func writeError(w http.ResponseWriter, r *http.Request, status int, code, message string) {
	writeJSON(w, status, response{
		Code: code, Message: message, RequestID: requestID(r), Data: nil,
	})
}

func writeJSON(w http.ResponseWriter, status int, value response) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		fmt.Printf("encode response: %v\n", err)
	}
}
