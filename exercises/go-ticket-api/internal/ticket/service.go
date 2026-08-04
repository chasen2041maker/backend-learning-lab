package ticket

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
	"unicode/utf8"
)

type Service struct {
	repository Repository
}

func NewService(repository Repository) *Service {
	return &Service{repository: repository}
}

func (s *Service) Create(ctx context.Context, tenantID string, input CreateInput) (Ticket, error) {
	title := strings.TrimSpace(input.Title)
	if tenantID == "" || title == "" || len(tenantID) > 64 || utf8.RuneCountInString(title) > 200 {
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
	value, err := s.repository.Get(ctx, tenantID, id)
	if err != nil {
		return Ticket{}, err
	}
	if value.TenantID != tenantID {
		// Hide cross-tenant resource existence.
		return Ticket{}, ErrNotFound
	}
	return value, nil
}

func (s *Service) List(ctx context.Context, tenantID string, limit int) ([]Ticket, error) {
	if limit < 1 || limit > 100 {
		return nil, ErrInvalidInput
	}
	values, err := s.repository.List(ctx, tenantID, limit)
	if err != nil {
		return nil, fmt.Errorf("list tickets: %w", err)
	}
	return values, nil
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
	updated, err := s.repository.Update(ctx, tenantID, value, expectedVersion)
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
	raw[6] = (raw[6] & 0x0f) | 0x40
	raw[8] = (raw[8] & 0x3f) | 0x80
	encoded := hex.EncodeToString(raw)
	return fmt.Sprintf(
		"%s-%s-%s-%s-%s",
		encoded[0:8],
		encoded[8:12],
		encoded[12:16],
		encoded[16:20],
		encoded[20:32],
	), nil
}
