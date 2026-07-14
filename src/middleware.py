"""ASGI middleware for mcp-humanizer.

NOTE: Pure ASGI middleware only. Starlette's BaseHTTPMiddleware buffers
the response body and breaks MCP's Streamable HTTP transport — see
CLAUDE.md key constraint #2.
"""

import json
import sys
import time
from datetime import datetime, timezone


class CFConnectingIPLogMiddleware:
    """Log one JSON line per HTTP request to stdout.

    Required for public MCPs: every request logs the client IP from
    Cloudflare's CF-Connecting-IP header so the access trail is visible
    in `docker logs` and any future log shipper.

    Intercepts only `http.response.start` to capture the status code;
    request and response bodies pass through untouched so streaming
    responses (SSE) keep working.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        method = scope.get("method", "")
        path = scope.get("path", "")
        client_ip = _header_value(scope, b"cf-connecting-ip") or "unknown"
        captured = {"status": 0}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                captured["status"] = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "ip": client_ip,
                "method": method,
                "path": path,
                "status": captured["status"],
                "duration_ms": round((time.monotonic() - start) * 1000, 2),
            }
            sys.stdout.write(json.dumps(record, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def _header_value(scope, name: bytes) -> str | None:
    """Look up a header in an ASGI scope. Header names are bytes, lowercased."""
    for k, v in scope.get("headers", []):
        if k == name:
            return v.decode("latin-1")
    return None
