package main

import (
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/chasen2041maker/backend-learning-lab/exercises/go-ticket-api/internal/ticket"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	repository := ticket.NewMemoryRepository()
	service := ticket.NewService(repository)
	handler := ticket.NewHandler(service, logger)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	})
	handler.Register(mux)

	server := &http.Server{
		Addr:              "127.0.0.1:8080",
		Handler:           ticket.RequestContext(mux),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	logger.Info("server starting", "address", server.Addr)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Error("server stopped", "error", err)
		os.Exit(1)
	}
}
