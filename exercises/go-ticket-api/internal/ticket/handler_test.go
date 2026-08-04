package ticket

import (
	"bytes"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"testing"
)

func TestHandlerCreateAndGet(t *testing.T) {
	handler := NewHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	mux := http.NewServeMux()
	handler.Register(mux)
	server := httptest.NewServer(RequestContext(Authenticate(mux)))
	t.Cleanup(server.Close)

	body := []byte(`{"title":"Cannot sign in"}`)
	request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", bytes.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("X-Request-ID", "req_test")
	request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
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

	getRequest, err := http.NewRequest(http.MethodGet, server.URL+"/api/v1/tickets/"+created.Data.ID, nil)
	if err != nil {
		t.Fatalf("build get request: %v", err)
	}
	getRequest.Header.Set("Authorization", "Bearer lab-token-tenant-a")
	getResponse, err := http.DefaultClient.Do(getRequest)
	if err != nil {
		t.Fatalf("get request: %v", err)
	}
	defer getResponse.Body.Close()
	if getResponse.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", getResponse.StatusCode)
	}
}

func TestHandlerRejectsTrailingJSONAndUnknownFields(t *testing.T) {
	handler := NewHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	mux := http.NewServeMux()
	handler.Register(mux)
	server := httptest.NewServer(RequestContext(Authenticate(mux)))
	t.Cleanup(server.Close)

	tests := []struct {
		name       string
		body       string
		wantStatus int
		wantCode   string
	}{
		{name: "trailing json", body: `{"title":"Valid"}{"second":true}`, wantStatus: 400, wantCode: "invalid_json"},
		{name: "unknown field", body: `{"title":"Valid","extra":true}`, wantStatus: 422, wantCode: "invalid_ticket_input"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", bytes.NewBufferString(test.body))
			if err != nil {
				t.Fatal(err)
			}
			request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
			response, err := http.DefaultClient.Do(request)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			if response.StatusCode != test.wantStatus {
				t.Fatalf("expected %d, got %d", test.wantStatus, response.StatusCode)
			}
			var envelope struct {
				Code string `json:"code"`
			}
			if err := json.NewDecoder(response.Body).Decode(&envelope); err != nil {
				t.Fatal(err)
			}
			if envelope.Code != test.wantCode {
				t.Fatalf("expected code %s, got %s", test.wantCode, envelope.Code)
			}
		})
	}
}

func TestHandlerUsesAuthenticatedTenantAndListsOnlyItsTickets(t *testing.T) {
	handler := NewHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	mux := http.NewServeMux()
	handler.Register(mux)
	server := httptest.NewServer(RequestContext(Authenticate(mux)))
	t.Cleanup(server.Close)

	create := func(token, title string) Ticket {
		t.Helper()
		request, err := http.NewRequest(
			http.MethodPost,
			server.URL+"/api/v1/tickets",
			bytes.NewBufferString(`{"title":"`+title+`"}`),
		)
		if err != nil {
			t.Fatal(err)
		}
		request.Header.Set("Authorization", "Bearer "+token)
		response, err := http.DefaultClient.Do(request)
		if err != nil {
			t.Fatal(err)
		}
		defer response.Body.Close()
		var envelope struct {
			Data Ticket `json:"data"`
		}
		if err := json.NewDecoder(response.Body).Decode(&envelope); err != nil {
			t.Fatal(err)
		}
		return envelope.Data
	}

	ticketA := create("lab-token-tenant-a", "A")
	_ = create("lab-token-tenant-b", "B")

	listRequest, _ := http.NewRequest(http.MethodGet, server.URL+"/api/v1/tickets", nil)
	listRequest.Header.Set("Authorization", "Bearer lab-token-tenant-a")
	listResponse, err := http.DefaultClient.Do(listRequest)
	if err != nil {
		t.Fatal(err)
	}
	defer listResponse.Body.Close()
	var listed struct {
		Data []Ticket `json:"data"`
	}
	if err := json.NewDecoder(listResponse.Body).Decode(&listed); err != nil {
		t.Fatal(err)
	}
	if len(listed.Data) != 1 || listed.Data[0].ID != ticketA.ID {
		t.Fatalf("unexpected tenant-scoped list: %+v", listed.Data)
	}

	crossTenantRequest, _ := http.NewRequest(
		http.MethodGet,
		server.URL+"/api/v1/tickets/"+ticketA.ID,
		nil,
	)
	crossTenantRequest.Header.Set("Authorization", "Bearer lab-token-tenant-b")
	crossTenantResponse, err := http.DefaultClient.Do(crossTenantRequest)
	if err != nil {
		t.Fatal(err)
	}
	defer crossTenantResponse.Body.Close()
	if crossTenantResponse.StatusCode != http.StatusNotFound {
		t.Fatalf("expected cross-tenant 404, got %d", crossTenantResponse.StatusCode)
	}
}

func TestHandlerAcceptsUnicodeCharacterLimitAndRequiresAuth(t *testing.T) {
	handler := NewHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	mux := http.NewServeMux()
	handler.Register(mux)
	server := httptest.NewServer(RequestContext(Authenticate(mux)))
	t.Cleanup(server.Close)

	missingAuth, err := http.Post(server.URL+"/api/v1/tickets", "application/json", bytes.NewBufferString(`{"title":"No auth"}`))
	if err != nil {
		t.Fatal(err)
	}
	defer missingAuth.Body.Close()
	if missingAuth.StatusCode != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", missingAuth.StatusCode)
	}

	request, _ := http.NewRequest(
		http.MethodPost,
		server.URL+"/api/v1/tickets",
		bytes.NewBufferString(`{"title":"`+strings.Repeat("中", 100)+`"}`),
	)
	request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusCreated {
		t.Fatalf("expected unicode title 201, got %d", response.StatusCode)
	}
}

func TestSharedCreateContractCases(t *testing.T) {
	type repeatTitle struct {
		Text  string `json:"text"`
		Count int    `json:"count"`
	}
	type contractCase struct {
		Name           string          `json:"name"`
		Authorization  bool            `json:"authorization"`
		Body           json.RawMessage `json:"body"`
		RawBody        string          `json:"raw_body"`
		RepeatTitle    *repeatTitle    `json:"repeat_title"`
		ExpectedStatus int             `json:"expected_status"`
		ExpectedCode   string          `json:"expected_code"`
	}
	var contract struct {
		CreateCases []contractCase `json:"create_cases"`
	}
	_, currentFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("locate contract test file")
	}
	contractPath := filepath.Join(filepath.Dir(currentFile), "..", "..", "..", "..", "contracts", "http-cases.json")
	content, err := os.ReadFile(contractPath)
	if err != nil {
		t.Fatalf("read shared contract: %v", err)
	}
	if err := json.Unmarshal(content, &contract); err != nil {
		t.Fatalf("decode shared contract: %v", err)
	}

	handler := NewHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	mux := http.NewServeMux()
	handler.Register(mux)
	server := httptest.NewServer(RequestContext(Authenticate(mux)))
	t.Cleanup(server.Close)
	uuidV4 := regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)

	for _, test := range contract.CreateCases {
		t.Run(test.Name, func(t *testing.T) {
			body := []byte(test.RawBody)
			if test.RawBody == "" {
				body = test.Body
			}
			if test.RepeatTitle != nil {
				body, err = json.Marshal(map[string]string{
					"title": strings.Repeat(test.RepeatTitle.Text, test.RepeatTitle.Count),
				})
				if err != nil {
					t.Fatal(err)
				}
			}
			request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", bytes.NewReader(body))
			if err != nil {
				t.Fatal(err)
			}
			request.Header.Set("Content-Type", "application/json")
			if test.Authorization {
				request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
			}
			response, err := http.DefaultClient.Do(request)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			if response.StatusCode != test.ExpectedStatus {
				t.Fatalf("expected %d, got %d", test.ExpectedStatus, response.StatusCode)
			}
			var envelope struct {
				Code string `json:"code"`
				Data struct {
					ID string `json:"id"`
				} `json:"data"`
			}
			if err := json.NewDecoder(response.Body).Decode(&envelope); err != nil {
				t.Fatal(err)
			}
			if envelope.Code != test.ExpectedCode {
				t.Fatalf("expected code %s, got %s", test.ExpectedCode, envelope.Code)
			}
			if test.ExpectedStatus == http.StatusCreated && !uuidV4.MatchString(envelope.Data.ID) {
				t.Fatalf("expected UUID v4, got %q", envelope.Data.ID)
			}
		})
	}
}
