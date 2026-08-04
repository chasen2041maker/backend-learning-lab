package ticket

import (
	"context"
	"errors"
	"testing"
)

func TestServiceCreateGetClose(t *testing.T) {
	service := NewService(NewMemoryRepository())
	ctx := context.Background()

	created, err := service.Create(ctx, CreateInput{TenantID: "tenant_a", Title: "Cannot sign in"})
	if err != nil {
		t.Fatalf("create ticket: %v", err)
	}
	if created.Status != StatusOpen || created.Version != 1 {
		t.Fatalf("unexpected created ticket: %+v", created)
	}

	got, err := service.Get(ctx, created.ID, "tenant_a")
	if err != nil {
		t.Fatalf("get ticket: %v", err)
	}
	if got.Title != "Cannot sign in" {
		t.Fatalf("unexpected title: %s", got.Title)
	}

	closed, err := service.Close(ctx, created.ID, "tenant_a", 1)
	if err != nil {
		t.Fatalf("close ticket: %v", err)
	}
	if closed.Status != StatusClosed || closed.Version != 2 {
		t.Fatalf("unexpected closed ticket: %+v", closed)
	}
}

func TestServiceHidesCrossTenantTicket(t *testing.T) {
	service := NewService(NewMemoryRepository())
	created, err := service.Create(
		context.Background(),
		CreateInput{TenantID: "tenant_a", Title: "Private"},
	)
	if err != nil {
		t.Fatalf("create ticket: %v", err)
	}

	_, err = service.Get(context.Background(), created.ID, "tenant_b")
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected not found, got %v", err)
	}
}

func TestServiceRejectsInvalidInput(t *testing.T) {
	service := NewService(NewMemoryRepository())
	tests := []CreateInput{
		{TenantID: "", Title: "Title"},
		{TenantID: "tenant_a", Title: ""},
	}
	for _, input := range tests {
		if _, err := service.Create(context.Background(), input); !errors.Is(err, ErrInvalidInput) {
			t.Fatalf("input %+v: expected invalid input, got %v", input, err)
		}
	}
}

func TestServiceRejectsStaleVersion(t *testing.T) {
	service := NewService(NewMemoryRepository())
	created, err := service.Create(
		context.Background(),
		CreateInput{TenantID: "tenant_a", Title: "Versioned"},
	)
	if err != nil {
		t.Fatalf("create ticket: %v", err)
	}

	_, err = service.Close(context.Background(), created.ID, "tenant_a", 99)
	if !errors.Is(err, ErrVersionConflict) {
		t.Fatalf("expected version conflict, got %v", err)
	}
}
