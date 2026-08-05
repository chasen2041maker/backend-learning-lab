from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("METRICS_HOST", "127.0.0.1")
PORT = 8081
READY = True


class RequestCounter:
    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            self._value += 1

    def value(self) -> int:
        with self._lock:
            return self._value


REQUESTS = RequestCounter()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        REQUESTS.increment()
        if self.path == "/health":
            self._write(200, "ok\n")
        elif self.path == "/ready":
            self._write(200 if READY else 503, "ready\n" if READY else "not ready\n")
        elif self.path == "/metrics":
            body = "# TYPE lab_http_requests_total counter\n"
            body += f"lab_http_requests_total {REQUESTS.value()}\n"
            self._write(200, body, "text/plain; version=0.0.4")
        else:
            self._write(404, "not found\n")

    def _write(self, status: int, body: str, content_type: str = "text/plain") -> None:
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"metrics demo listening on http://{HOST}:{PORT}")
    server.serve_forever()
