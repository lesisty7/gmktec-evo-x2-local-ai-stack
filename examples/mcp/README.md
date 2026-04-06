# MCP Examples

This directory contains public-safe examples for using MCP with the ComfyUI image stack.

## Included Files

- `comfyui.env.example`
- `searxng.env.example`

## What It Shows

- how to configure `COMFYUI_BASE_URL`
- how to configure `SEARXNG_URL`
- how to keep model-specific defaults out of the script body
- how to adapt the MCP layer to either a local or remote service endpoint

## Important Detail

The published MCP scripts do not hardcode a private LAN IP.

Instead, they expect deployment-specific addressing to come from environment variables, especially:

- `COMFYUI_BASE_URL`
- `SEARXNG_URL`

That makes the scripts easier to publish, easier to reuse, and less tied to one homelab network.

## Related Files

- [../../docs/mcp-comfyui.md](../../docs/mcp-comfyui.md)
- [../../docs/mcp-codex.md](../../docs/mcp-codex.md)
- [../../docs/mcp-search.md](../../docs/mcp-search.md)
- [../../scripts/mcp/comfyui_mcp_v1.py](../../scripts/mcp/comfyui_mcp_v1.py)
- [../../scripts/mcp/comfyui_mcp_v2.py](../../scripts/mcp/comfyui_mcp_v2.py)
- [../../scripts/mcp/searxng_mcp.py](../../scripts/mcp/searxng_mcp.py)
