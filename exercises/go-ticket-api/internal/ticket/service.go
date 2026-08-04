package ticket

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

type Service struct {
	repository Repository
}

func NewService(repository Repository) *Service {
	return &Service{repository: repository}
}

func (s *Service) Create(ctx context.Context, input CreateInput) (Ticket, error) {
	tenantID := strings.TrimSpace(input.TenantID)
	title := strings.TrimSpace(input.Title)
	if tenantID == "" || title == "" || len(tenantID) > 64 || len(title) > 200 {
		return Ticket{}, ErrInvalidInput
	}

	id, err := newID()
	if err != nil {
		return Ticket{}, fmt.Errorf("generate ticket id: %w", err)
	}
	now := time.Now().UTC()
	value := Ticket{
		ID:        id,
		TenantID:  tenantID,
		Title:     title,
		Status:    StatusOpen,
		Version:   1,
		CreatedAt: now,
		UpdatedAt: now,
	}
	created, err := s.repository.Create(ctx, value)
	if err != nil {
		return Ticket{}, fmt.Errorf("create ticket: %w", err)
	}
	return created, nil
}

func (s *Service) Get(ctx context.Context, id, tenantID string) (Ticket, error) {
	value, err := s.repository.Get(ctx, id)
	if err != nil {
		return Ticket{}, err
	}
	if value.TenantID != tenantID {
		// Hide cross-tenant resource existence.
		return Ticket{}, ErrNotFound
	}
	return value, nil
}

func (s *Service) Close(
	ctx context.Context,
	id, tenantID string,
	expectedVersion int64,
) (Ticket, error) {
	value, err := s.Get(ctx, id, tenantID)
	if err != nil {
		return Ticket{}, err
	}
	if value.Status == StatusClosed {
		return Ticket{}, ErrStateConflict
	}
	if expectedVersion < 1 {
		return Ticket{}, ErrInvalidInput
	}
	if value.Version != expectedVersion {
		return Ticket{}, ErrVersionConflict
	}
	value.Status = StatusClosed
	value.Version++
	value.UpdatedAt = time.Now().UTC()
	updated, err := s.repository.Update(ctx, value, expectedVersion)
	if err != nil {
		return Ticket{}, fmt.Errorf("update ticket: %w", err)
	}
	return updated, nil
}

func newID() (string, error) {
	raw := make([]byte, 16)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	return hex.EncodeToString(raw), nil
}
