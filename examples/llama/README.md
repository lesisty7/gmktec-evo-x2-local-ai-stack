# llama.cpp Examples

This directory contains the public-safe configuration examples that support the `llama.cpp` backend described in this repository.

## Files

- `router.env.example`
- `models.ini.example`
- `models.ini.example2`

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

[Unsloth](https://huggingface.co/unsloth) is a good source for ready-to-use GGUF model builds.

As a practical rule of thumb:

- `Q5_K_XL` is usually a good compromise with a bias toward quality
- `Q4_K_XL` is usually a good compromise with a bias toward smaller size and lower memory use

That does not replace testing, but it is a reasonable default heuristic when building a mixed local model inventory.

## What Each File Does

### `router.env.example`

Holds runtime environment for:

- ROCm paths
- cache locations
- router host and port
- default model directory
- location of the built `llama-server` binary
- optional GPU-specific overrides such as `HSA_OVERRIDE_GFX_VERSION`

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

The included script is a public-safe reference, not a promise that every ROCm system should use exactly the same GPU target or override values.

The public filename was simplified to `update-llama.sh`, but the underlying logic is intentionally kept close to the working source version used in the reference stack.

For a real deployment, verify:

- your ROCm install path
- your effective GPU architecture target
- whether you actually need `HSA_OVERRIDE_GFX_VERSION`
