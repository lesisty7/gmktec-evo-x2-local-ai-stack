# Search MCP Server

This document describes the public-safe MCP search server included in this repository.

The reference script is:

- [../scripts/mcp/searxng_mcp.py](../scripts/mcp/searxng_mcp.py)

## Purpose

This MCP server exposes a web-search tool backed by a SearXNG instance.

Its primary use is to give an MCP-capable client a controlled way to:

- search the web
- verify changing information
- look up documentation
- retrieve recent sources through a local search gateway

## Tool Surface

The main tool is:

- `search_web`

It supports parameters such as:

- query
- max results
- language
- categories
- safesearch
- engines
- time range

## Addressing and Endpoint Handling

As with the ComfyUI MCP examples, the public version should not hardcode a private LAN address.

For that reason, the public script uses:

- `SEARXNG_URL`

with a safe default of:

- `http://127.0.0.1:8080/search`

That default is appropriate if:

- SearXNG runs on the same machine
- a loopback or local proxy endpoint is exposed there

If your SearXNG instance runs elsewhere, override it explicitly:

```bash
export SEARXNG_URL="http://your-search-host:8080/search"
```

## Why This Pattern Is Worth Publishing

The useful part is not just the script itself. The useful part is the pattern:

- keep the script logic stable
- keep network addressing in environment variables
- keep defaults safe for publication
- avoid baking private infrastructure assumptions into the code body

## Configuration Example

See:

- [../examples/mcp/searxng.env.example](../examples/mcp/searxng.env.example)
- [../examples/mcp/README.md](../examples/mcp/README.md)
- [../examples/stacks/search/README.md](../examples/stacks/search/README.md)
- [../examples/stacks/search/docker-compose.example.yml](../examples/stacks/search/docker-compose.example.yml)
- [../examples/stacks/search/searxng/settings.yml.example](../examples/stacks/search/searxng/settings.yml.example)
- [mcp-codex.md](mcp-codex.md)

## Practical Recommendation

For a public example repository, this is a good split:

1. run SearXNG as a normal service
2. point the MCP server at it through `SEARXNG_URL`
3. tune categories, engines, and safesearch through environment variables
4. keep the MCP script itself generic and publishable

In this repository, the recommended public-safe pairing is:

- backend service example: [../examples/stacks/search/README.md](../examples/stacks/search/README.md)
- MCP client example: [../examples/mcp/searxng.env.example](../examples/mcp/searxng.env.example)

For Codex-specific configuration examples, see [mcp-codex.md](mcp-codex.md).
