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

## Published Tool Surface

### `v1`

| Tool | Purpose | Main inputs |
| --- | --- | --- |
| `generate_image` | Basic checkpoint-based text-to-image generation | `prompt_text`, `width`, `height`, `steps`, `cfg`, `output_format` |
| `unload_models` | Trigger ComfyUI `/free` | `unload_models`, `free_memory` |

### `v2`

| Tool | Purpose | Main inputs |
| --- | --- | --- |
| `generate_image` | Preferred Flux text-to-image path | `prompt_text`, `preset`, `width`, `height`, `steps`, `cfg` |
| `generate_image_i2i` | Image-to-image generation | `input_image_path`, `prompt_text`, `denoise`, `preset` |
| `generate_image_edit` | Prompt-guided edit path | `input_image_path`, `edit_instruction`, `denoise`, `preset` |
| `generate_image_inpaint` | Masked image editing | `input_image_path`, `mask_image_path`, `prompt_text`, `denoise` |
| `generate_image_outpaint` | Canvas expansion around an image | `input_image_path`, `top`, `right`, `bottom`, `left`, `denoise` |
| `generate_image_upscale` | Lightweight post-upscale path | `input_image_path`, `upscale_model` |
| `unload_models` | Trigger ComfyUI `/free` | `unload_models`, `free_memory` |

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
- [mcp-codex.md](mcp-codex.md)

Those files show the intended public-safe configuration pattern:

- keep ComfyUI addressing in environment variables
- keep model names in environment variables where useful
- avoid baking private network assumptions into the script body

If you want to wire this into Codex specifically, see [mcp-codex.md](mcp-codex.md) for example `~/.codex/config.toml` sections.

## Relationship to the Media Stack

These MCP scripts assume a running ComfyUI instance.

For the container shape of that stack, see:

- [../examples/stacks/media/README.md](../examples/stacks/media/README.md)
- [../examples/stacks/media/docker-compose.example.yml](../examples/stacks/media/docker-compose.example.yml)

If you also want manual UI workflows instead of MCP-only usage, see:

- [../examples/comfyui-workflows/README.md](../examples/comfyui-workflows/README.md)

Those exported workflow JSON files are intended to be placed in the normal ComfyUI workflow directory:

- `/opt/ComfyUI/user/default/workflows`

or, when using the mounted user directory pattern from the example stack:

- `${COMFYUI_DATA_ROOT}/user/default/workflows`

For simplified visual references of those workflow families, see [comfyui-workflow-diagrams.md](comfyui-workflow-diagrams.md).

Important limitation:

- the exported workflow JSON files in this repository should be treated as untested examples
- they may require fixes, model-name changes, node replacement, or full replacement with better workflows imported from inside ComfyUI itself
- do not assume they will work unchanged on a different machine, image tag, or node set

## Important Upgrade Warning

Be careful with `ComfyUI Manager -> Update All`.

In stacks that mount the ComfyUI application directory from persistent storage, Manager can update the ComfyUI code and custom nodes without updating the Docker image that provides the Python, ROCm, and PyTorch runtime.

That can leave the installation in a mixed state where:

- the ComfyUI code is newer
- the custom nodes are newer
- the Docker image is older
- the runtime inside the image is no longer compatible with the updated code

In practice, that can lead to container restarts, runtime crashes, failed generations, or broken custom node imports.

If that happens, a common recovery path is to update the Docker image to a compatible newer image instead of trying to keep an old image with newly updated ComfyUI code.

## Practical Recommendation

For a public example repository, the cleanest pattern is:

1. run ComfyUI as a normal service
2. point MCP at it through `COMFYUI_BASE_URL`
3. keep model-specific defaults in environment variables
4. treat `v1` as fallback and `v2` as the richer default path
