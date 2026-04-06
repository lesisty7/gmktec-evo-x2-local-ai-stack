# Examples

This directory contains public-safe example configuration files.

## Principles

- examples should be useful, but not private
- examples should be minimal and readable
- examples should not contain live tokens, internal endpoints, or personal infrastructure details

## Current Examples

### `comfyui-workflows/`

- exported workflow JSON files
- [README.md](comfyui-workflows/README.md)

This gives a small, practical set of manual ComfyUI workflows that can be copied into a ComfyUI `user/default/workflows` directory instead of rebuilding the graphs from scratch.

### `mcp/`

- `comfyui.env.example`
- `searxng.env.example`
- [README.md](mcp/README.md)

This shows the public-safe configuration pattern for MCP-based ComfyUI and search clients and keeps addressing details outside the script body.

### `llama/`

- `models.ini.example`
- `router.env.example`
- [README.md](llama/README.md)

These show the shape of a router-mode `llama.cpp` setup without exposing a private deployment.

### `stacks/automation/`

- `.env.example`
- `docker-compose.example.yml`
- [README.md](stacks/automation/README.md)

This captures the categories of settings commonly found in an automation stack, but with all private endpoints, IPs, and tokens replaced by placeholders. It now also includes a public-safe Docker Compose example and the small `python-runner` sidecar used by the reference stack.

### `stacks/mattermost/`

- `.env.example`
- `docker-compose.example.yml`
- [README.md](stacks/mattermost/README.md)

This captures the bootstrap and persistence shape of a Mattermost deployment without exposing real credentials, URLs, or operator identities.

### `stacks/media/`

- `.env.example`
- [README.md](stacks/media/README.md)
- `docker-compose.example.yml`

This shows the shape of a ComfyUI stack for AMD hardware with persistent mounts. The example now includes a companion `.env.example` so paths, ports, and image tags can be adjusted without turning the compose file into a host-specific export. See also [comfyui-workflows/README.md](comfyui-workflows/README.md) for manual workflow JSON files and where to place them.

### `stacks/mcp-playwright/`

- `.env.example`
- [README.md](stacks/mcp-playwright/README.md)

This keeps a small MCP Playwright example separate and easy to understand without pulling in unrelated stack details.

### `stacks/qdrant/`

- `.env.example`
- `docker-compose.example.yml`
- [README.md](stacks/qdrant/README.md)

This gives a compact example for a Qdrant deployment with optional backup-related settings and sanitized remote references.

### `stacks/search/`

- `.env.example`
- `docker-compose.example.yml`
- `searxng/settings.yml.example`
- [README.md](stacks/search/README.md)

This gives a compact SearXNG deployment example that complements the MCP search server example. Together they show both halves of the search path: the backend service and the MCP client that calls it.

### `stacks/rocketchat/`

- `.env.example`
- `docker-compose.example.yml`
- [README.md](stacks/rocketchat/README.md)

This captures the shape of a Rocket.Chat deployment with MongoDB and SMTP wiring, but with all live URLs and credentials replaced.
