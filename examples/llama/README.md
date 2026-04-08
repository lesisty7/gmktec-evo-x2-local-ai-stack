# llama.cpp Examples

This directory contains the public-safe configuration examples that support the `llama.cpp` backend described in this repository.

These files are meant to be understood together with the published helper scripts, not as a separate standalone mini-guide:

- [../../scripts/llama/update-llama.sh](../../scripts/llama/update-llama.sh)
- [../../scripts/llama/update-llama-vulkan.sh](../../scripts/llama/update-llama-vulkan.sh)

In practice, `router.env.example`, `models.ini.example`, and the update script form one operational bundle.

## Files

- `router.env.example`
- `models.ini.example`
- `models.ini.example2`

The current public-safe default path is `Vulkan`, while `HIP/ROCm` is kept as a documented fallback path rather than being removed.

## Required Runtime Directories

The reference layout expects these directories to exist on the AI runtime host or LXC:

- `/etc/llama`
- `/opt/llama.cpp`
- `/mnt/ai-models/llm`
- `/mnt/ai-models/cache/llama.cpp`
- `/mnt/ai-models/cache/hf`

## Important: Models Are Not Included

This repository does not include LLM model files.

To make the backend actually usable, the operator must:

1. download their own GGUF models into `/mnt/ai-models/llm`
2. edit `models.ini` so it points to the models they really downloaded

The example `models.ini.example` is only a template. It is not meant to be used unchanged.

## Practical Model Download Flow

In the reference setup, model downloads should be done inside the Ubuntu LXC, not on the Proxmox host.

Typical target directory:

```bash
cd /mnt/ai-models/llm
```

Example downloads:

```bash
wget -c -O Qwen3.5-27B-UD-Q6_K_XL.gguf \
  "https://huggingface.co/unsloth/Qwen3.5-27B-GGUF/resolve/main/Qwen3.5-27B-UD-Q6_K_XL.gguf?download=true"

wget -c -O Qwen3.5-9B-UD-Q6_K_XL.gguf \
  "https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-UD-Q6_K_XL.gguf?download=true"

wget -c -O Qwen3-Coder-Next-UD-Q4_K_XL.gguf \
  "https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF/resolve/main/Qwen3-Coder-Next-UD-Q4_K_XL.gguf?download=true"

wget -c -O gemma-4-26B-A4B-it-UD-Q5_K_XL.gguf \
  "https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/resolve/main/gemma-4-26B-A4B-it-UD-Q5_K_XL.gguf?download=true"
```

After downloading, update `models.ini` so the preset names and paths match the models you actually keep in `/mnt/ai-models/llm`.

## Newer Nemotron Option

If you are reviewing newer large-context candidates, also look at:

- base model: `nvidia/Nemotron-Cascade-2-30B-A3B`
- GGUF builds: `bartowski/nvidia_Nemotron-Cascade-2-30B-A3B-GGUF`

Reference links:

- <https://huggingface.co/nvidia/Nemotron-Cascade-2-30B-A3B>
- <https://huggingface.co/bartowski/nvidia_Nemotron-Cascade-2-30B-A3B-GGUF>

It looks like a very promising option for a modern local router lineup, especially if you want a stronger successor candidate next to or instead of older Nemotron presets.

## Practical Quantization Guidance

[Unsloth](https://huggingface.co/unsloth) and [bartowski](https://huggingface.co/bartowski) are both good sources for ready-to-use GGUF model builds.

As a practical rule of thumb:

- `Q5_K_XL` is usually a good compromise with a bias toward quality
- `Q4_K_XL` is usually a good compromise with a bias toward smaller size and lower memory use

That does not replace testing, but it is a reasonable default heuristic when building a mixed local model inventory.

## Router Capacity Note

In the reference setup, router mode is intentionally configured to keep only one model active at a time.

That is controlled in `router.env` by:

```env
LLAMA_MODELS_MAX=1
```

This is a deliberate memory-management choice, not a universal requirement. If you increase it, plan for higher concurrent RAM and VRAM usage.

## What Each File Does

### `router.env.example`

Holds runtime environment for:

- ROCm paths
- current backend-selection state
- cache locations
- router host and port
- default model directory
- location of the built `llama-server` binary
- optional GPU-specific overrides such as `HSA_OVERRIDE_GFX_VERSION`

The current example points to `build-vulkan` because that was the verified working backend in the refreshed reference environment.

### `models.ini.example`

Holds router presets for:

- chat models
- coding models
- multimodal models
- embeddings models
- idle shutdown policy through `sleep-idle-seconds`

In practice, this file is expected to be edited by the operator. The example values are only placeholders showing the structure.

### `models.ini.example2`

This is a more realistic reference example based on a mixed production-style model inventory:

- large chat / instruct models
- coding models
- multimodal models with `mmproj`
- embeddings models
- idle memory recycling through `sleep-idle-seconds`

Use it when you want to start from a layout that is closer to a real router configuration rather than from the smaller generic template.

It is still not a drop-in file. You must remove presets for models you do not have and adjust settings to your hardware budget.

## Related Files

- [../../docs/llama-backend.md](../../docs/llama-backend.md)
- [../../docs/memory-recycling.md](../../docs/memory-recycling.md)
- [../../scripts/llama/update-llama.sh](../../scripts/llama/update-llama.sh)

## Practical Note

The included scripts are public-safe references, not a promise that every AMD system should use exactly the same backend, GPU target, or override values.

The public filename stays simple as `update-llama.sh`, and a dedicated `update-llama-vulkan.sh` wrapper is also included because Vulkan is currently the known-good default in the published reference setup.

For a real deployment, verify:

- your ROCm install path
- your effective GPU architecture target
- whether you actually need `HSA_OVERRIDE_GFX_VERSION`
- whether Vulkan or HIP/ROCm is actually the stable backend on your own machine
