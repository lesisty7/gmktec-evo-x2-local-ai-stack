# Adding MCP Servers to Codex

This document shows the configuration pattern for adding the published MCP examples to Codex.

It is based on the actual structure of a working `~/.codex/config.toml`, but rewritten into a public-safe form.

## Where This Goes

Add MCP server definitions under:

- `~/.codex/config.toml`

using sections shaped like:

```toml
[mcp_servers.some-name]
command = "/path/to/python3"
args = ["/path/to/server.py"]
```

## Practical Pattern

In the reference setup, the Codex config uses one section per MCP server under `mcp_servers.*`.

For example:

```toml
[mcp_servers.local-comfy]
command = "/path/to/python3"
args = ["/path/to/repo/scripts/mcp/comfyui_mcp_v1.py"]
env = { "COMFYUI_BASE_URL" = "http://127.0.0.1:8188" }

[mcp_servers.local-comfy-v2]
command = "/path/to/python3"
args = ["/path/to/repo/scripts/mcp/comfyui_mcp_v2.py"]
env = {
  "COMFYUI_BASE_URL" = "http://127.0.0.1:8188",
  "FLUX2_UNET" = "flux-2-klein-9b-Q5_K_M.gguf",
  "FLUX2_TEXT_ENCODER" = "qwen_3_8b_fp4mixed.safetensors",
  "FLUX2_VAE" = "flux2-vae.safetensors"
}

[mcp_servers.local-search]
command = "/path/to/python3"
args = ["/path/to/repo/scripts/mcp/searxng_mcp.py"]
env = {
  "SEARXNG_URL" = "http://127.0.0.1:8080/search",
  "LANGUAGE" = "en",
  "CATEGORIES" = "general,it,dev"
}
```

## Notes on `command`

The reference Codex config uses a Python interpreter directly as the command and passes the MCP script path in `args`.

That is a good pattern to copy.

Typical options are:

- a dedicated virtualenv Python
- a system `python3`

Examples:

```toml
command = "/home/your-user/venvs/mcp/bin/python"
```

or:

```toml
command = "/usr/bin/python3"
```

## Notes on `args`

Point `args` to the published script file in this repository, for example:

```toml
args = ["/path/to/repo/scripts/mcp/comfyui_mcp_v2.py"]
```

Keep the server path explicit. That makes the config easier to audit and easier to move between machines.

## Why `env` Matters

For the published MCP examples, environment variables are the right place for host-specific details.

Use `env` in Codex config to provide:

- `COMFYUI_BASE_URL`
- `SEARXNG_URL`
- model names when needed

That keeps the script bodies publishable and keeps deployment-specific assumptions in one obvious place.

## Minimal Example

If you only want the preferred image workflow plus search:

```toml
[mcp_servers.local-comfy-v2]
command = "/usr/bin/python3"
args = ["/path/to/repo/scripts/mcp/comfyui_mcp_v2.py"]
env = { "COMFYUI_BASE_URL" = "http://127.0.0.1:8188" }

[mcp_servers.local-search]
command = "/usr/bin/python3"
args = ["/path/to/repo/scripts/mcp/searxng_mcp.py"]
env = { "SEARXNG_URL" = "http://127.0.0.1:8080/search" }
```

## Published MCP Servers and Tools

| Server | Script | Main tools |
| --- | --- | --- |
| `local-comfy` | `scripts/mcp/comfyui_mcp_v1.py` | `generate_image`, `unload_models` |
| `local-comfy-v2` | `scripts/mcp/comfyui_mcp_v2.py` | `generate_image`, `generate_image_i2i`, `generate_image_edit`, `generate_image_inpaint`, `generate_image_outpaint`, `generate_image_upscale`, `unload_models` |
| `local-search` | `scripts/mcp/searxng_mcp.py` | `search_web` |

For argument-level details, see:

- [mcp-comfyui.md](mcp-comfyui.md)
- [mcp-search.md](mcp-search.md)

## Related Files

- [mcp-comfyui.md](mcp-comfyui.md)
- [mcp-search.md](mcp-search.md)
- [../examples/mcp/README.md](../examples/mcp/README.md)
