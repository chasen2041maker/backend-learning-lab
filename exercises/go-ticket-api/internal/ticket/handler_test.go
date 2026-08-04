package ticket

import (
	"bytes"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHandlerCreateAndGet(t *testing.T) {
	handler := NewHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	mux := http.NewServeMux()
	handler.Register(mux)
	server := httptest.NewServer(RequestContext(mux))
	t.Cleanup(server.Close)

	body := []byte(`{"tenant_id":"tenant_a","title":"Cannot sign in"}`)
	request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", bytes.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("X-Request-ID", "req_test")
	createdResponse, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatalf("create request: %v", err)
	}
	defer createdResponse.Body.Close()
	if createdResponse.StatusCode != http.StatusCreated {
		t.Fatalf("expected 201, got %d", createdResponse.StatusCode)
	}
	if createdResponse.Header.Get("X-Request-ID") != "req_test" {
		t.Fatalf("request id was not propagated")
	}

	var created struct {
		Data Ticket `json:"data"`
	}
	if err := json.NewDecoder(createdResponse.Body).Decode(&created); err != nil {
		t.Fatalf("decode response: %v", err)
	}

	getResponse, err := http.Get(server.URL + "/api/v1/tickets/" + created.Data.ID + "?tenant_id=tenant_a")
	if err != nil {
		t.Fatalf("get request: %v", err)
	}
	defer getResponse.Body.Close()
	if getResponse.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", getResponse.StatusCode)
	}
}
