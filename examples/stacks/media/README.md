# Media Stack Example

This directory contains a public-safe example of the `media` stack shape used by the reference project.

## What It Shows

- a ComfyUI container for AMD hardware
- persistent model mounts
- persistent app data mounts
- a small idle-unloader sidecar
- a companion `.env.example` for paths, ports, and image tags
- a matching pattern for storing manual workflow JSON files

## What It Does Not Guarantee

- exact compatibility with your hardware
- exact compatibility with your ROCm stack
- exact compatibility with every custom node

## How to Use It

- copy `.env.example` to `.env`
- treat it as a structural example
- adapt paths to your own storage layout
- review image tags and environment variables for your own platform
- replace any environment-specific assumptions before real deployment
- if you want manual ComfyUI workflows, copy the exported JSON files into your ComfyUI workflow directory

## Notes

- examples in this repository are intentionally conservative and documentation-oriented
- they should be reviewed before use in a live environment
- the reference stack also uses idle-based ComfyUI unloading; see [../../../docs/memory-recycling.md](../../../docs/memory-recycling.md)
- MCP-based ComfyUI usage is documented separately in [../../../docs/mcp-comfyui.md](../../../docs/mcp-comfyui.md)
- manual workflow examples are documented in [../../comfyui-workflows/README.md](../../comfyui-workflows/README.md)
- in the compose example, the effective workflow destination is `${COMFYUI_DATA_ROOT}/user/default/workflows`
- Manager-based in-app updates can break the installation if the ComfyUI code gets ahead of the Docker image runtime
- if a Manager update breaks generation, updating the Docker image is often a better recovery path than trying to keep an old image with newly updated ComfyUI code
