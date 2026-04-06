# Search Stack Example

This directory contains a public-safe example of the `search` stack used by the reference project.

## What It Shows

- a minimal SearXNG deployment
- a small Redis sidecar
- a bind-mounted SearXNG settings directory
- a separate persistent data directory for SearXNG state and logs
- the connection point between the SearXNG service and the MCP search script

## Included Files

- `.env.example`
- `docker-compose.example.yml`
- `searxng/settings.yml.example`

## Why This Matters

The MCP search server in this repository is only half of the picture.

To make the search MCP example operational, you also need a running search backend.
This example shows the deployment shape for that backend.

## How to Use It

1. Copy `.env.example` to `.env`.
2. Copy `searxng/settings.yml.example` to `searxng/settings.yml`.
3. Replace `replace_with_random_secret_key` with your own generated secret.
4. Adjust ports, paths, and network names for your environment.
5. Start the stack with Docker Compose.
6. Point the MCP search script at the resulting endpoint through `SEARXNG_URL`.

## Expected MCP Endpoint

The MCP search script expects a SearXNG search endpoint such as:

- `http://127.0.0.1:8080/search`

If your SearXNG service runs elsewhere, replace it with the real host and port.

## Important Notes

- `formats` must include `json` if you want to use the MCP search server against this SearXNG instance.
- The example is intentionally minimal and conservative.
- You should review enabled engines, safe-search policy, and network exposure for your own deployment.
- The example network name is just a placeholder and should be adapted to your Docker layout.

## Related Files

- [../../../docs/mcp-search.md](../../../docs/mcp-search.md)
- [../../mcp/searxng.env.example](../../mcp/searxng.env.example)
- [../../../scripts/mcp/searxng_mcp.py](../../../scripts/mcp/searxng_mcp.py)
