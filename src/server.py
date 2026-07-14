"""mcp-humanizer server entry point."""

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from src.middleware import CFConnectingIPLogMiddleware
from src.storage.json_store import init_storage
from src.tools.check import register_check_tools
from src.tools.read import register_read_tools

PORT = int(os.environ.get("PORT", "8016"))
HOST = os.environ.get("HOST", "0.0.0.0")
# Public hostname this server is served under, used for DNS-rebinding
# protection. Set PUBLIC_HOST to your own domain when deploying behind a
# reverse proxy or tunnel; the localhost entries cover local development.
PUBLIC_HOST = os.environ.get("PUBLIC_HOST", "mcp-humanizer.example.com")
ALLOWED_HOSTS = [PUBLIC_HOST, f"localhost:{PORT}", f"127.0.0.1:{PORT}"]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

SERVER_INSTRUCTIONS = (
    "Rules and a deterministic checker for making written prose read as human, "
    "not machine-generated. Use this whenever you are drafting or revising prose "
    "for a human reader (articles, emails, marketing, cover letters, docs, "
    "narrative) and it matters that the result not sound AI-generated.\n"
    "Workflow (the loop is required, not optional polish): (1) call "
    "humanizer_get_summary for a quick edit, or humanizer_get_guide for a major "
    "writing task; (2) write or revise the draft; (3) call humanizer_check_text "
    "on your draft and resolve every finding; (4) re-run humanizer_check_text "
    "until prohibitions_clear is true, then self-attest the manual_review items. "
    "Reading the rules alone leaves roughly half the violations in place; the "
    "check->fix loop is what carries adherence (see foundation.primary_usage)."
)

mcp = FastMCP(
    "humanizer_mcp",
    instructions=SERVER_INSTRUCTIONS,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=ALLOWED_HOSTS,
    ),
)

logger.info("Initializing storage layer")
init_storage()

logger.info("Registering read tools")
register_read_tools(mcp)

logger.info("Registering check tools")
register_check_tools(mcp)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting mcp-humanizer on {HOST}:{PORT}")
    # CRITICAL: Use uvicorn.run() with the ASGI app directly.
    # Do NOT use mcp.run() — it ignores HOST/PORT env vars and
    # defaults to 127.0.0.1:8000, which is unreachable from outside the container.
    app = CFConnectingIPLogMiddleware(mcp.streamable_http_app())
    uvicorn.run(app, host=HOST, port=PORT)
