# GMKtec Evo-X2 Local AI Stack

Reference documentation and example files for a local AI workstation and homelab stack built around the GMKtec Evo-X2.

## At a Glance

- hardware reference: `GMKtec Evo-X2`, `Ryzen AI Max+ 395`, `Radeon 8060S`, `128 GB RAM`
- platform shape: `Proxmox -> privileged Ubuntu LXC -> Docker`
- LLM path: `llama.cpp` in router mode, built for HIP/ROCm
- image path: `ComfyUI` with `FLUX.2 klein 9B Q5 GGUF`
- fallback image path: `Juggernaut XL Lightning`
- video path: `LTX 2.3`
- storage shape: `ZFS`, mirrored NVMe, dedicated model and app-data trees

## Scope

This repository is intended to document and eventually share:

- the overall architecture of a Proxmox-based local AI stack
- the split between host, LXC, and Docker workloads
- practical llama.cpp router-mode patterns for AMD hardware
- a documented model layout for both LLM and diffusion workloads
- a curated ComfyUI image and video workflow setup
- public-safe example configs and templates

## Who This Is For

This repository is being shaped for people who want to build a similar system and care about:

- a local-first AI workstation or homelab design
- Proxmox plus LXC rather than a full GPU VM
- llama.cpp for local LLM serving
- ComfyUI for image and video work
- predictable storage layout for models and persistent service data

It is not trying to be:

- a one-command installer
- a complete mirror of a private production setup
- a universal best-practice document for every homelab

## High-Level Architecture

The working design is based on three layers:

1. Proxmox VE host
2. an Ubuntu LXC container with direct access to AMD GPU devices
3. Dockerized application stacks inside that LXC

Key ideas:

- keep the Proxmox host lean
- run llama.cpp close to the metal inside the LXC
- run web tools and helper services in Docker
- persist models and application data on mounted storage
- separate LLM and diffusion assets under a predictable directory layout

## Start Here

Recommended reading order:

1. [docs/from-scratch.md](docs/from-scratch.md)
2. [docs/architecture.md](docs/architecture.md)
3. [docs/stack-overview.md](docs/stack-overview.md)
4. [docs/service-boundaries.md](docs/service-boundaries.md)
5. [docs/llama-backend.md](docs/llama-backend.md)
6. [docs/memory-recycling.md](docs/memory-recycling.md)
7. [docs/lxc-layout.md](docs/lxc-layout.md)
8. [docs/model-layout.md](docs/model-layout.md)
9. [docs/proxmox-zfs-helper.md](docs/proxmox-zfs-helper.md)
10. [docs/publication-readiness-checklist.md](docs/publication-readiness-checklist.md)

## From-Scratch Starting Point

The documented reference machine is not treated as a stock Windows mini PC.

The intended starting point is:

- `GMKtec Evo-X2`
- `AMD Ryzen AI Max+ 395`
- `Radeon 8060S / gfx1151`
- `128 GB RAM`
- original Windows SSD removed
- `2 x 4 TB NVMe` used for a mirrored Proxmox ZFS install

The public docs now capture that baseline so a reader can understand the machine assumptions before looking at LXC, Docker, or model layout details.

## Quick Start for Readers

If you are opening this repository fresh and want the shortest path to understanding it:

1. read [docs/from-scratch.md](docs/from-scratch.md)
2. read [docs/architecture.md](docs/architecture.md)
3. read [docs/llama-backend.md](docs/llama-backend.md)
4. inspect [examples/llama/README.md](examples/llama/README.md)
5. inspect [scripts/llama/update-llama.sh](scripts/llama/update-llama.sh)

That sequence covers the machine assumptions, the host/LXC split, the current `llama.cpp` operating model, the required directories, and the reference build/update workflow.

## Current Operating Defaults

The reference stack currently leans toward:

- `llama.cpp` in router mode for LLM serving
- ComfyUI for image and video workflows
- `FLUX.2 klein 9B Q5 GGUF` as the preferred image path
- `Juggernaut XL Lightning` as a fallback image path
- `LTX 2.3` as the current video path

## Repository Layout

```text
GMKtec-Evo-X2-public/
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE.md
├── README.md
├── SECURITY.md
├── STATUS.md
├── scripts/
│   ├── README.md
│   └── llama/
│       └── update-llama.sh
├── docs/
│   ├── architecture.md
│   ├── faq.md
│   ├── from-scratch.md
│   ├── hardware-and-platform.md
│   ├── llama-backend.md
│   ├── lxc-layout.md
│   ├── memory-recycling.md
│   ├── images/
│   │   ├── proxmox-disks.png
│   │   └── proxmox-network.png
│   ├── README.md
│   ├── model-layout.md
│   ├── proxmox-zfs-helper.md
│   ├── publication-readiness-checklist.md
│   ├── release-scope.md
│   ├── roadmap.md
│   ├── screenshot-review.md
│   ├── service-boundaries.md
│   ├── stack-overview.md
│   └── storage-layout.md
└── examples/
    ├── README.md
    ├── llama/
    │   ├── models.ini.example
    │   ├── README.md
    │   └── router.env.example
    └── stacks/
        ├── automation/
        │   ├── .env.example
        │   └── README.md
        ├── mattermost/
        │   ├── .env.example
        │   └── README.md
        ├── mcp-playwright/
        │   ├── .env.example
        │   └── README.md
        ├── media/
        │   ├── .env.example
        │   ├── README.md
        │   └── docker-compose.example.yml
        ├── qdrant/
        │   ├── .env.example
        │   └── README.md
        └── rocketchat/
            ├── .env.example
            └── README.md
```

## Where To Look for `llama.cpp`

The `llama.cpp` path is now documented in three layers:

- operational overview: [docs/llama-backend.md](docs/llama-backend.md)
- config examples and required directories: [examples/llama/README.md](examples/llama/README.md)
- public-safe management script: [scripts/llama/update-llama.sh](scripts/llama/update-llama.sh)

The backend document also includes the current script help, so a reader can see the CLI surface without running anything locally.

One important assumption is explicit: this repository does not include model files. A user must download models into the expected directory and adapt `models.ini` to their own inventory.

The public draft now includes all three parts needed to explain the current `llama.cpp` path coherently:

- documentation
- sanitized example config
- a reference management script

## Models

The current reference stack uses a dedicated shared models tree split into:

- `llm/` for GGUF language, embedding, and multimodal models
- `sd/` for diffusion checkpoints, UNet, text encoders, LoRAs, VAE, and related assets
- `cache/` for Hugging Face and llama.cpp caches

The documented model tree is intentionally included as a public example because the structure itself is useful. It shows not only single-file models, but also directory-shaped multimodal models and symlink-based deduplication patterns.

See:

- [docs/model-layout.md](docs/model-layout.md)
- [docs/model-tree-snapshot.md](docs/model-tree-snapshot.md)
- [examples/README.md](examples/README.md)

## Documentation and Safety

Additional repository guidance is documented in:

- [docs/README.md](docs/README.md)
- [docs/publication-readiness-checklist.md](docs/publication-readiness-checklist.md)
- [SECURITY.md](SECURITY.md)
- [LICENSE.md](LICENSE.md)

## License and Risk

This repository is provided as free software and free documentation:

- free software and free documentation
- use at your own risk
- no warranty
- documentation and examples may contain mistakes or become outdated

See [LICENSE.md](LICENSE.md).
