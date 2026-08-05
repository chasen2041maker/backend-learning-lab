package main

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/chasen2041maker/backend-learning-lab/exercises/go-ticket-api/internal/ticket"
)

func main() {
	if err := run("127.0.0.1:8080"); err != nil {
		slog.Error("server failed", "error", err)
		os.Exit(1)
	}
}

func run(address string) error {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	repository := ticket.NewMemoryRepository()
	service := ticket.NewService(repository)

	server := &http.Server{
		Addr:              address,
		Handler:           ticket.NewHTTPHandler(service, logger),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}
	logger.Info("server starting", "address", server.Addr)

	shutdownSignal, stop := signal.NotifyContext(
		context.Background(),
		os.Interrupt,
		syscall.SIGTERM,
	)
	defer stop()
	serverError := make(chan error, 1)
	go func() {
		serverError <- server.ListenAndServe()
	}()

	select {
	case err := <-serverError:
		if err != nil && err != http.ErrServerClosed {
			return fmt.Errorf("listen: %w", err)
		}
	case <-shutdownSignal.Done():
		logger.Info("shutdown signal received")
	}

	shutdownContext, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(shutdownContext); err != nil {
		return fmt.Errorf("graceful shutdown: %w", err)
	}
	logger.Info("server stopped")
	return nil
}
