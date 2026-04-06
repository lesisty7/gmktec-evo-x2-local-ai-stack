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
