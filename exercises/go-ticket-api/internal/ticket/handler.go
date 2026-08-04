package ticket

import (
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
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
	mux.HandleFunc("GET /api/v1/tickets/{id}", h.get)
	mux.HandleFunc("POST /api/v1/tickets/{id}/close", h.close)
}

func (h *Handler) create(w http.ResponseWriter, r *http.Request) {
	var input CreateInput
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&input); err != nil {
		writeError(w, r, http.StatusBadRequest, "invalid_json", "invalid request body")
		return
	}

	value, err := h.service.Create(r.Context(), input)
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
	value, err := h.service.Get(r.Context(), r.PathValue("id"), r.URL.Query().Get("tenant_id"))
	if err != nil {
		h.handleError(w, r, err)
		return
	}
	writeJSON(w, http.StatusOK, response{
		Code: "ok", Message: "ok", RequestID: requestID(r), Data: value,
	})
}

func (h *Handler) close(w http.ResponseWriter, r *http.Request) {
	var input CloseInput
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&input); err != nil {
		writeError(w, r, http.StatusBadRequest, "invalid_json", "invalid request body")
		return
	}
	value, err := h.service.Close(
		r.Context(),
		r.PathValue("id"),
		input.TenantID,
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
	case errors.Is(err, ErrInvalidInput):
		writeError(w, r, http.StatusBadRequest, "invalid_ticket_input", err.Error())
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
