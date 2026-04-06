# ComfyUI Workflow Examples

This directory contains exported manual workflow JSON files from the reference stack.

They are useful when you want to:

- import working workflows into the ComfyUI UI
- keep a small curated workflow library under version control
- reuse the same workflow shapes described by the MCP examples

## Included Workflows

### Flux image workflows

- `flux2_klein_9b_q5_gguf_t2i.json`
- `flux2_klein_9b_q5_gguf_i2i.json`
- `flux2_klein_9b_q5_gguf_edit.json`
- `flux2_klein_9b_q5_gguf_inpaint.json`
- `flux2_klein_9b_q5_gguf_outpaint.json`
- `flux2_ultrasharp_upscale.json`

### LTX video workflows

- `ltx_2_3_t2v_fast.json`
- `ltx_2_3_i2v_short.json`

## Where to Put Them

The typical ComfyUI workflow directory is:

- `/opt/ComfyUI/user/default/workflows`

If your container mounts the ComfyUI user directory from the host, place them under the mounted `user/default/workflows` path instead.

In the example media stack from this repository, that means:

- `${COMFYUI_DATA_ROOT}/user/default/workflows`

because the compose example mounts:

- `${COMFYUI_DATA_ROOT}/user:/opt/ComfyUI/user`

## How to Use Them

1. Copy one or more workflow JSON files into your ComfyUI workflow directory.
2. Refresh or reopen ComfyUI.
3. Open the workflow from the UI workflow list.
4. Adjust model filenames, prompt text, output paths, and any host-specific assumptions.

## Important Notes

- These are example workflows, not a promise of universal compatibility.
- Model filenames must match your own installed files.
- Flux and LTX workflows require the matching model family and supporting files.
- Public examples use the workflow shape from the reference stack, but you should still validate them in your own environment.
