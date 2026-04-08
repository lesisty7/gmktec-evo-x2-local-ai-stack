# Scripts

This directory contains public-safe helper scripts that are useful enough to publish as part of the first release.

The goal is not to dump every local operational script. The goal is to keep only the scripts that help explain or reproduce the core architecture.

## Current Contents

### `llama/update-llama.sh`

A public-safe `llama.cpp` manager script for:

- cloning or updating `llama.cpp`
- building the current default backend
- protecting operator-owned config files
- switching between folder scanning and INI preset mode
- updating the `systemd` service

The current public version defaults to `Vulkan` because that was the verified working backend in the refreshed reference environment. `HIP/ROCm` remains available through `LLAMA_BACKEND=hip`.

Treat it as a reference implementation and adapt it to your own paths and packaging decisions.

### `llama/update-llama-vulkan.sh`

A very small wrapper that runs `update-llama.sh` with `LLAMA_BACKEND=vulkan`.

It exists mainly to make the currently working backend explicit in public documentation.

### `obsolete/`

Historical or older reference scripts that are still worth preserving for comparison are moved under `obsolete/` instead of being deleted.

### `mcp/comfyui_mcp_v1.py`

A public-safe MCP server script that exposes a simple ComfyUI image generation path.

### `mcp/comfyui_mcp_v2.py`

A richer public-safe MCP server script for a newer ComfyUI image workflow, including i2i, edit, inpaint, outpaint, upscale, and model unloading.

### `mcp/searxng_mcp.py`

A public-safe MCP search server script backed by SearXNG, intended for current-information lookup and documentation search.

## Python Dependencies

The published MCP scripts share a small dependency set.

See:

- [mcp/requirements.txt](mcp/requirements.txt)

Install them into the Python environment used by your MCP client, for example:

```bash
pip install -r scripts/mcp/requirements.txt
```
