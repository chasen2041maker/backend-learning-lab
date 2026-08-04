from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REQUESTS = 0
READY = True


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global REQUESTS
        REQUESTS += 1
        if self.path == "/health":
            self._write(200, "ok\n")
        elif self.path == "/ready":
            self._write(200 if READY else 503, "ready\n" if READY else "not ready\n")
        elif self.path == "/metrics":
            body = "# TYPE lab_http_requests_total counter\n"
            body += f"lab_http_requests_total {REQUESTS}\n"
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
    server = ThreadingHTTPServer(("0.0.0.0", 8081), Handler)
    print("metrics demo listening on http://127.0.0.1:8081")
    server.serve_forever()
