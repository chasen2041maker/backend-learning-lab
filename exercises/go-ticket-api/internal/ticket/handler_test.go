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
	"strconv"
	"strings"
	"testing"
	"time"
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

func TestHTTPHandlerHealthIsPublicAndAPIRequiresAuthentication(t *testing.T) {
	handler := NewHTTPHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil)))
	tests := []struct {
		name       string
		method     string
		path       string
		wantStatus int
		wantCode   string
	}{
		{name: "health is public", method: http.MethodGet, path: "/health", wantStatus: http.StatusOK},
		{
			name:       "ticket API requires authentication",
			method:     http.MethodGet,
			path:       "/api/v1/tickets",
			wantStatus: http.StatusUnauthorized,
			wantCode:   "authentication_required",
		},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			recorder := httptest.NewRecorder()
			request := httptest.NewRequest(test.method, test.path, nil)
			handler.ServeHTTP(recorder, request)
			if recorder.Code != test.wantStatus {
				t.Fatalf("expected %d, got %d", test.wantStatus, recorder.Code)
			}
			if test.wantCode != "" {
				var envelope struct {
					Code string `json:"code"`
				}
				if err := json.NewDecoder(recorder.Body).Decode(&envelope); err != nil {
					t.Fatal(err)
				}
				if envelope.Code != test.wantCode {
					t.Fatalf("expected code %s, got %s", test.wantCode, envelope.Code)
				}
			}
		})
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
		Text   string `json:"text"`
		Count  int    `json:"count"`
		Prefix string `json:"prefix"`
		Suffix string `json:"suffix"`
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
					"title": test.RepeatTitle.Prefix + strings.Repeat(test.RepeatTitle.Text, test.RepeatTitle.Count) + test.RepeatTitle.Suffix,
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

func TestSharedEndpointContractsAreDeclared(t *testing.T) {
	_, currentFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("locate contract test file")
	}
	contractPath := filepath.Join(filepath.Dir(currentFile), "..", "..", "..", "..", "contracts", "http-cases.json")
	content, err := os.ReadFile(contractPath)
	if err != nil {
		t.Fatalf("read shared contract: %v", err)
	}
	var contract struct {
		HealthCases []json.RawMessage `json:"health_cases"`
		GetCases    []json.RawMessage `json:"get_cases"`
		ListCases   []json.RawMessage `json:"list_cases"`
		CloseCases  []json.RawMessage `json:"close_cases"`
	}
	if err := json.Unmarshal(content, &contract); err != nil {
		t.Fatalf("decode shared contract: %v", err)
	}
	for name, cases := range map[string][]json.RawMessage{
		"health": contract.HealthCases,
		"get":    contract.GetCases,
		"list":   contract.ListCases,
		"close":  contract.CloseCases,
	} {
		if len(cases) == 0 {
			t.Errorf("%s endpoint contract cases are missing", name)
		}
	}
}

func TestSharedEndpointContractCases(t *testing.T) {
	type healthCase struct {
		Name           string `json:"name"`
		Authorization  bool   `json:"authorization"`
		ExpectedStatus int    `json:"expected_status"`
		ExpectedBody   struct {
			Status string `json:"status"`
		} `json:"expected_body"`
	}
	type getCase struct {
		Name           string `json:"name"`
		TicketID       string `json:"ticket_id"`
		SeedTitle      string `json:"seed_title"`
		SeedTenant     string `json:"seed_tenant"`
		RequestTenant  string `json:"request_tenant"`
		ExpectedStatus int    `json:"expected_status"`
		ExpectedCode   string `json:"expected_code"`
	}
	type listCase struct {
		Name           string   `json:"name"`
		SeedTitles     []string `json:"seed_titles"`
		Limit          int      `json:"limit"`
		ExpectedStatus int      `json:"expected_status"`
		ExpectedCode   string   `json:"expected_code"`
		ExpectedTitles []string `json:"expected_titles"`
	}
	type closeCase struct {
		Name            string `json:"name"`
		TicketID        string `json:"ticket_id"`
		SeedTitle       string `json:"seed_title"`
		PrecloseVersion int64  `json:"preclose_version"`
		ExpectedVersion int64  `json:"expected_version"`
		RawBody         string `json:"raw_body"`
		ExpectedStatus  int    `json:"expected_status"`
		ExpectedCode    string `json:"expected_code"`
	}
	var contract struct {
		HealthCases []healthCase `json:"health_cases"`
		GetCases    []getCase    `json:"get_cases"`
		ListCases   []listCase   `json:"list_cases"`
		CloseCases  []closeCase  `json:"close_cases"`
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

	t.Run("health", func(t *testing.T) {
		server := httptest.NewServer(NewHTTPHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil))))
		t.Cleanup(server.Close)
		for _, test := range contract.HealthCases {
			request, err := http.NewRequest(http.MethodGet, server.URL+"/health", nil)
			if err != nil {
				t.Fatal(err)
			}
			if test.Authorization {
				request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
			}
			response, err := http.DefaultClient.Do(request)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			if response.StatusCode != test.ExpectedStatus {
				t.Fatalf("%s: expected %d, got %d", test.Name, test.ExpectedStatus, response.StatusCode)
			}
			var body struct {
				Status string `json:"status"`
			}
			if err := json.NewDecoder(response.Body).Decode(&body); err != nil {
				t.Fatal(err)
			}
			if body.Status != test.ExpectedBody.Status {
				t.Fatalf("%s: expected body status %q, got %q", test.Name, test.ExpectedBody.Status, body.Status)
			}
		}
	})

	t.Run("get", func(t *testing.T) {
		for _, test := range contract.GetCases {
			server := httptest.NewServer(NewHTTPHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil))))
			t.Cleanup(server.Close)
			ticketID := test.TicketID
			if test.SeedTitle != "" {
				request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", strings.NewReader(`{"title":"`+test.SeedTitle+`"}`))
				if err != nil {
					t.Fatal(err)
				}
				seedToken := "lab-token-tenant-b"
				if test.SeedTenant == "tenant_a" {
					seedToken = "lab-token-tenant-a"
				}
				request.Header.Set("Authorization", "Bearer "+seedToken)
				response, err := http.DefaultClient.Do(request)
				if err != nil {
					t.Fatal(err)
				}
				var created struct {
					Data Ticket `json:"data"`
				}
				if err := json.NewDecoder(response.Body).Decode(&created); err != nil {
					t.Fatal(err)
				}
				response.Body.Close()
				ticketID = created.Data.ID
			}
			request, err := http.NewRequest(http.MethodGet, server.URL+"/api/v1/tickets/"+ticketID, nil)
			if err != nil {
				t.Fatal(err)
			}
			requestToken := "lab-token-tenant-a"
			if test.RequestTenant == "tenant_b" {
				requestToken = "lab-token-tenant-b"
			}
			request.Header.Set("Authorization", "Bearer "+requestToken)
			response, err := http.DefaultClient.Do(request)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			var envelope struct {
				Code string `json:"code"`
			}
			if err := json.NewDecoder(response.Body).Decode(&envelope); err != nil {
				t.Fatal(err)
			}
			if response.StatusCode != test.ExpectedStatus || envelope.Code != test.ExpectedCode {
				t.Fatalf("%s: got status=%d code=%s", test.Name, response.StatusCode, envelope.Code)
			}
		}
	})

	for _, test := range contract.ListCases {
		test := test
		t.Run("list/"+test.Name, func(t *testing.T) {
			server := httptest.NewServer(NewHTTPHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil))))
			t.Cleanup(server.Close)
			for index, title := range test.SeedTitles {
				if index > 0 {
					time.Sleep(time.Millisecond)
				}
				request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", strings.NewReader(`{"title":"`+title+`"}`))
				if err != nil {
					t.Fatal(err)
				}
				request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
				response, err := http.DefaultClient.Do(request)
				if err != nil {
					t.Fatal(err)
				}
				response.Body.Close()
			}
			request, err := http.NewRequest(http.MethodGet, server.URL+"/api/v1/tickets?limit="+strconv.Itoa(test.Limit), nil)
			if err != nil {
				t.Fatal(err)
			}
			request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
			response, err := http.DefaultClient.Do(request)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			var envelope struct {
				Code string   `json:"code"`
				Data []Ticket `json:"data"`
			}
			if err := json.NewDecoder(response.Body).Decode(&envelope); err != nil {
				t.Fatal(err)
			}
			if response.StatusCode != test.ExpectedStatus || envelope.Code != test.ExpectedCode {
				t.Fatalf("%s: got status=%d code=%s", test.Name, response.StatusCode, envelope.Code)
			}
			if len(test.ExpectedTitles) > 0 {
				got := make([]string, 0, len(envelope.Data))
				for _, value := range envelope.Data {
					got = append(got, value.Title)
				}
				if strings.Join(got, "\x00") != strings.Join(test.ExpectedTitles, "\x00") {
					t.Fatalf("%s: expected titles %v, got %v", test.Name, test.ExpectedTitles, got)
				}
			}
		})
	}

	for _, test := range contract.CloseCases {
		test := test
		t.Run("close/"+test.Name, func(t *testing.T) {
			server := httptest.NewServer(NewHTTPHandler(NewService(NewMemoryRepository()), slog.New(slog.NewTextHandler(io.Discard, nil))))
			t.Cleanup(server.Close)
			ticketID := test.TicketID
			if test.SeedTitle != "" {
				request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets", strings.NewReader(`{"title":"`+test.SeedTitle+`"}`))
				if err != nil {
					t.Fatal(err)
				}
				request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
				response, err := http.DefaultClient.Do(request)
				if err != nil {
					t.Fatal(err)
				}
				var created struct {
					Data Ticket `json:"data"`
				}
				if err := json.NewDecoder(response.Body).Decode(&created); err != nil {
					t.Fatal(err)
				}
				response.Body.Close()
				ticketID = created.Data.ID
			}
			if test.PrecloseVersion > 0 {
				request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets/"+ticketID+"/close", strings.NewReader(`{"expected_version":`+strconv.FormatInt(test.PrecloseVersion, 10)+`}`))
				if err != nil {
					t.Fatal(err)
				}
				request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
				response, err := http.DefaultClient.Do(request)
				if err != nil {
					t.Fatal(err)
				}
				response.Body.Close()
				if response.StatusCode != http.StatusOK {
					t.Fatalf("%s: preclose status=%d", test.Name, response.StatusCode)
				}
			}
			body := test.RawBody
			if body == "" {
				body = `{"expected_version":` + strconv.FormatInt(test.ExpectedVersion, 10) + `}`
			}
			request, err := http.NewRequest(http.MethodPost, server.URL+"/api/v1/tickets/"+ticketID+"/close", strings.NewReader(body))
			if err != nil {
				t.Fatal(err)
			}
			request.Header.Set("Authorization", "Bearer lab-token-tenant-a")
			response, err := http.DefaultClient.Do(request)
			if err != nil {
				t.Fatal(err)
			}
			defer response.Body.Close()
			var envelope struct {
				Code string `json:"code"`
			}
			if err := json.NewDecoder(response.Body).Decode(&envelope); err != nil {
				t.Fatal(err)
			}
			if response.StatusCode != test.ExpectedStatus || envelope.Code != test.ExpectedCode {
				t.Fatalf("%s: got status=%d code=%s", test.Name, response.StatusCode, envelope.Code)
			}
		})
	}
}
