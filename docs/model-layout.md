# Model Layout

This document records the current logical model layout used by the reference stack.

## Overview

The models tree is divided into:

- `cache/`
- `llm/`
- `sd/`

## LLM Area

The `llm/` tree contains:

- chat and instruct GGUF models
- embedding models
- multimodal GGUF models
- model directories containing both `model.gguf` and `mmproj.gguf`

That last point is worth making explicit: not every useful model layout is a flat list of single files. Some multimodal models are better represented as a small directory containing the paired assets that belong together.

Representative categories currently present:

- general instruct models
- coding models
- embeddings
- vision-language models
- reranker-style multimodal assets

## Diffusion Area

The `sd/` tree contains:

- `checkpoints/`
- `clip/`
- `text_encoders/`
- `unet/`
- `loras/`
- `vae/`
- `upscale_models/`
- `controlnet/`
- `embeddings/`
- `archive/`

## Current Active Direction

Image generation:

- preferred path: `FLUX.2 klein 9B Q5 GGUF`
- fallback path: `Juggernaut XL Lightning`

Video generation:

- current path: `LTX 2.3`

## Quantization Policy

Preferred policy:

- use quantized models almost always
- use `Q5_K_M` for important image models
- use `Q4_K_M` for larger or lower-priority models
- avoid keeping multiple quantizations of the same model unless they serve a clear purpose

## Operational Pattern

The reference stack also uses a few simple organizational habits that are worth copying:

- keep active models separate from archived models
- use symlinks when a legacy filename still has compatibility value
- keep diffusion support assets such as text encoders, LoRAs, and VAE files in predictable subtrees
- avoid storing multiple near-identical copies of the same large asset without a concrete reason

## Current Tree Snapshot

This is a publishable reference example, not a distribution manifest.

It is intentionally useful as documentation because it shows:

- flat single-file GGUF storage for standard LLMs
- two-file directory layouts for multimodal models
- a split between active and archived diffusion assets
- symlink-based compatibility for renamed or deduplicated large files

See [model-tree-snapshot.md](model-tree-snapshot.md) for the current documented tree.
