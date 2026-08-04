package ticket

import "errors"

var (
	ErrNotFound        = errors.New("ticket not found")
	ErrInvalidInput    = errors.New("invalid ticket input")
	ErrStateConflict   = errors.New("ticket state conflict")
	ErrVersionConflict = errors.New("ticket version conflict")
)
