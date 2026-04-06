# Stack Overview

This document describes the stack by function rather than by file or container name.

## Main Functional Areas

### LLM serving

Handled by llama.cpp in router mode with model presets.

Typical use cases:

- chat
- coding assistance
- embeddings
- multimodal experiments

See also:

- [llama-backend.md](llama-backend.md)
- [service-boundaries.md](service-boundaries.md)

### Image generation

Handled by ComfyUI with:

- a preferred modern GGUF workflow path
- a simpler fallback checkpoint path
- curated manual workflows for generation and editing

Current operating bias:

- preferred path: `FLUX.2 klein 9B Q5 GGUF`
- fallback path: `Juggernaut XL Lightning`

### Video generation

Handled by a curated `LTX 2.3` workflow path for:

- text-to-video
- image-to-video

Current operating bias:

- default path: `LTX 2.3`
- manual workflows are treated as curated operator workflows rather than raw upstream templates

### Supporting services

The reference stack also includes additional services such as:

- automation
- search
- vector storage
- web UI layers
- reverse proxy

This public draft intentionally describes the system at a high level instead of exposing private deployment details.

## Design Pattern in One Sentence

The stack keeps low-level hardware-adjacent AI runtime concerns in the LXC, while higher-level user-facing services are composed and managed inside Docker.
