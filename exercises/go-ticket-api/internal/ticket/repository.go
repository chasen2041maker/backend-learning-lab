package ticket

import (
	"context"
	"sync"
)

type Repository interface {
	Create(ctx context.Context, value Ticket) (Ticket, error)
	Get(ctx context.Context, id string) (Ticket, error)
	Update(ctx context.Context, value Ticket, expectedVersion int64) (Ticket, error)
}

type MemoryRepository struct {
	mu      sync.RWMutex
	tickets map[string]Ticket
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{tickets: make(map[string]Ticket)}
}

func (r *MemoryRepository) Create(ctx context.Context, value Ticket) (Ticket, error) {
	if err := ctx.Err(); err != nil {
		return Ticket{}, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	r.tickets[value.ID] = value
	return value, nil
}

func (r *MemoryRepository) Get(ctx context.Context, id string) (Ticket, error) {
	if err := ctx.Err(); err != nil {
		return Ticket{}, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	value, ok := r.tickets[id]
	if !ok {
		return Ticket{}, ErrNotFound
	}
	return value, nil
}

func (r *MemoryRepository) Update(
	ctx context.Context,
	value Ticket,
	expectedVersion int64,
) (Ticket, error) {
	if err := ctx.Err(); err != nil {
		return Ticket{}, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	current, ok := r.tickets[value.ID]
	if !ok {
		return Ticket{}, ErrNotFound
	}
	if current.Version != expectedVersion {
		return Ticket{}, ErrVersionConflict
	}
	r.tickets[value.ID] = value
	return value, nil
}
