# mcp-humanizer: Deployment Guide

This server is a stateless, public, read-only MCP. It runs well as a single
container behind any HTTPS reverse proxy or tunnel. The steps below use Docker
Compose and a Cloudflare Tunnel, but nothing here depends on that specific
setup.

## Configuration

The container is configured entirely through environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `PORT` | Port the server listens on | `8016` |
| `HOST` | Bind address inside the container | `0.0.0.0` |
| `PUBLIC_HOST` | Public hostname, used for DNS-rebinding protection | `mcp-humanizer.example.com` |
| `GITHUB_TOKEN` | Read-only token so the entrypoint can pull the latest `data/` on start | none |
| `GITHUB_REPO` | Repo the entrypoint pulls `data/` from | none |

Set `PUBLIC_HOST` to the hostname you serve the MCP under. The allowlist in
`src/server.py` combines it with the localhost entries, so a mismatch returns
`421` on every request. If `GITHUB_TOKEN` and `GITHUB_REPO` are unset, the
container simply serves the `data/` baked into the image.

## docker-compose.yml

The `docker-compose.yml` at the repo root is the build and runtime source of
truth. Provide secrets through an `env_file` or your host's secret manager
rather than committing them. The container runs as a non-root user with all
Linux capabilities dropped and `no-new-privileges` set.

## Data updates

There are no runtime write tools. To change the rules, edit the JSON files in
`data/`, commit, and push. The entrypoint runs `git fetch` and `reset --hard`
inside `/app/data` on every container start, so a restart picks up the latest
data:

```bash
docker restart mcp-humanizer
```

For a code or dependency change, rebuild the image:

```bash
docker compose build && docker compose up -d
```

## Reverse proxy or tunnel

Point your proxy or tunnel at `http://localhost:8016` (or whatever `PORT` you
set). A Cloudflare Tunnel is a good fit because it needs no inbound firewall
ports and keeps the origin address private: route your hostname to
`http://localhost:8016` in the tunnel config.

Because DNS-rebinding protection is on, the proxy must forward the original
`Host` header (most do by default). If every request returns `421`, a rewritten
`Host` header is the usual cause.

## Connecting a client

Point any MCP client at `https://<your-host>/mcp` with no auth. In Claude.ai:

1. Settings, then Connectors, then Add custom connector
2. Name it (for example, `Text Humanizer MCP`)
3. Remote MCP server URL: `https://<your-host>/mcp`
4. Leave the OAuth fields empty
5. Add

## Verifying a deployment

A healthy start logs the storage init, tool registration, and the uvicorn bind
line. Each request writes one JSON access line to stdout.

A vanilla `GET` is expected to return `406`, because the Streamable HTTP
transport rejects it:

```bash
curl -v https://<your-host>/mcp
```

A `406` from outside your network confirms the server is listening and the
route works. For a full check, add the connector and call a read tool such as
`humanizer_get_summary`.
