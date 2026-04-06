# Storage Layout

## Top-Level Layout

A practical split for this type of system is:

- `/mnt/ai-models/llm`
- `/mnt/ai-models/sd`
- `/mnt/ai-models/cache`
- `/mnt/containers/*`
- `/opt/stacks/*`

## Current Source Layout

The current reference stack uses:

- separate model mounts for `llm`, `sd`, and `cache`
- a dedicated data mount per major service in `/mnt/containers`
- stack definitions under `/opt/stacks`

This is somewhat over-engineered for small setups, but it gives clear ownership boundaries and makes per-service persistence easier to reason about.

## Purpose of Each Area

### `llm`

Use for:

- GGUF chat models
- embedding models
- multimodal models with `model.gguf` and `mmproj.gguf`

### `sd`

Use for:

- diffusion checkpoints
- UNet models
- CLIP and text encoders
- LoRAs
- VAE assets
- upscale models

### `cache`

Use for:

- Hugging Face cache
- llama.cpp cache
- other reproducible transient caches

### `containers`

Use for:

- application state
- persistent service data
- user workflows
- generated output

### `opt/stacks`

Use for:

- compose files
- service-specific helpers
- stack-local scripts

## ZFS Tuning and SSD Practicality

For SSD-backed systems, the most important idea is not to chase exotic tuning, but to avoid unnecessary write amplification and unnecessary metadata churn.

Useful examples:

- `atime=off`
- `dedup=off`
- `copies=1`
- `compression=lz4` for app data
- `compression=off` for already-compressed large model files

Practical interpretation:

- `atime=off` avoids updating file access timestamps on every read
- this reduces pointless metadata writes and is usually a good default for model storage
- `compression=lz4` is a good baseline for many application datasets
- `compression=off` can make sense for large binary model files that do not compress meaningfully
- `recordsize=1M` is a practical fit for large sequential model files
- `recordsize=16K` is a more typical application-data setting

## Current Source ZFS Bias

Observed in the current reference stack:

- model datasets use settings optimized for large binary files
- container datasets use settings closer to normal application data
- model datasets currently also use `sync=disabled`

Important note:

- `sync=disabled` can improve throughput, but it is a durability trade-off
- it should be treated as an explicit risk decision, not as a universal recommendation
