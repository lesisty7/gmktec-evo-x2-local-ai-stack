# ComfyUI MCP Servers

This document explains the practical MCP layer used to expose ComfyUI image generation tools to MCP-capable clients.

The reference stack currently uses two script variants:

- `scripts/mcp/comfyui_mcp_v1.py`
- `scripts/mcp/comfyui_mcp_v2.py`

## Purpose

These scripts expose ComfyUI workflows as MCP tools so an MCP client can request:

- text-to-image generation
- image-to-image generation
- prompt-guided image editing
- inpaint and outpaint
- upscale
- model unloading through ComfyUI `/free`

## `v1` and `v2`

### `v1`

`v1` is the simpler path.

It is built around a basic checkpoint workflow and is useful as a conservative fallback server.

In the reference stack, this path is associated with a classic checkpoint-style image workflow.

### `v2`

`v2` is the preferred path.

It exposes a richer tool surface around the newer Flux-based image pipeline and includes tools such as:

- `generate_image`
- `generate_image_i2i`
- `generate_image_edit`
- `generate_image_inpaint`
- `generate_image_outpaint`
- `generate_image_upscale`
- `unload_models`

## Addressing and IP Handling

The most important publication detail is that the MCP scripts should not hardcode a private LAN address.

For that reason, the public copies use:

- `COMFYUI_BASE_URL`

with a safe default of:

- `http://127.0.0.1:8188`

That default is appropriate when:

- the MCP server runs on the same machine as ComfyUI
- a local reverse proxy or loopback mapping exists

If ComfyUI runs elsewhere, set `COMFYUI_BASE_URL` explicitly, for example:

```bash
export COMFYUI_BASE_URL="http://your-comfyui-host:8188"
```

This is the preferred public documentation pattern because it separates:

- script logic
- deployment-specific network addressing

## Script Files

Published reference scripts:

- [../scripts/mcp/comfyui_mcp_v1.py](../scripts/mcp/comfyui_mcp_v1.py)
- [../scripts/mcp/comfyui_mcp_v2.py](../scripts/mcp/comfyui_mcp_v2.py)

These public copies are based on working internal scripts, but the default base URL has been sanitized and externalized through environment variables.

## Configuration Example

See:

- [../examples/mcp/README.md](../examples/mcp/README.md)
- [../examples/mcp/comfyui.env.example](../examples/mcp/comfyui.env.example)

Those files show the intended public-safe configuration pattern:

- keep ComfyUI addressing in environment variables
- keep model names in environment variables where useful
- avoid baking private network assumptions into the script body

## Relationship to the Media Stack

These MCP scripts assume a running ComfyUI instance.

For the container shape of that stack, see:

- [../examples/stacks/media/README.md](../examples/stacks/media/README.md)
- [../examples/stacks/media/docker-compose.example.yml](../examples/stacks/media/docker-compose.example.yml)

## Practical Recommendation

For a public example repository, the cleanest pattern is:

1. run ComfyUI as a normal service
2. point MCP at it through `COMFYUI_BASE_URL`
3. keep model-specific defaults in environment variables
4. treat `v1` as fallback and `v2` as the richer default path
