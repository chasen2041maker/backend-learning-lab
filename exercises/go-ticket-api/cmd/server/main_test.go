package main

import (
	"net"
	"strings"
	"testing"
)

func TestRunReturnsListenError(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("reserve test address: %v", err)
	}
	defer listener.Close()

	err = run(listener.Addr().String())
	if err == nil {
		t.Fatal("expected run to return a listen error")
	}
	if !strings.Contains(err.Error(), "listen") {
		t.Fatalf("expected listen error, got %v", err)
	}
}
