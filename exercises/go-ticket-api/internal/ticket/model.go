package ticket

import "time"

type Status string

const (
	StatusOpen   Status = "open"
	StatusClosed Status = "closed"
)

type Ticket struct {
	ID        string    `json:"id"`
	TenantID  string    `json:"tenant_id"`
	Title     string    `json:"title"`
	Status    Status    `json:"status"`
	Version   int64     `json:"version"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type CreateInput struct {
	Title string `json:"title"`
}

type CloseInput struct {
	ExpectedVersion int64 `json:"expected_version"`
}

type Principal struct {
	Subject  string
	TenantID string
}
