# Architecture

## Goal

Build a practical local AI stack on GMKtec Evo-X2 hardware that supports:

- local LLM serving
- embeddings and multimodal inference
- image generation and editing
- short-form local video generation
- Docker-based AI tooling around the core inference services

This architecture assumes the machine is being used as a dedicated Proxmox-based AI host rather than as a retained Windows installation with occasional AI workloads layered on top.

## Deployment Model

The stack is split into layers.

## Layer Diagram

```mermaid
flowchart TD
    A[GMKtec Evo-X2 hardware\nCPU + iGPU + RAM + SSDs]
    B[Proxmox VE host\nZFS storage + device exposure]
    C[Privileged Ubuntu LXC\nAI runtime container]
    D[llama.cpp on the LXC OS\nrouter mode]
    E[Docker inside LXC]
    F[ComfyUI]
    G[OpenWebUI and related tools]
    H[Automation, search,\nvector DB, proxy, support services]
    I[/mnt/ai-models\nllm + sd + cache]
    J[/mnt/containers\npersistent app data]
    K[/opt/stacks\ncompose definitions]

    A --> B
    B --> C
    B --> I
    B --> J
    C --> D
    C --> E
    C --> I
    C --> J
    C --> K
    E --> F
    E --> G
    E --> H
```

## Practical Reading of the Diagram

- the physical PC provides CPU, GPU, RAM, and storage
- Proxmox owns the host OS, storage layout, and hardware exposure
- the main AI LXC is the working runtime boundary for AI workloads
- llama.cpp runs directly in the LXC user space rather than in Docker
- Docker inside the LXC hosts user-facing and helper services
- models and persistent service data live on mounted storage instead of inside ephemeral containers

### 1. Proxmox host

The hypervisor handles:

- storage
- container lifecycle
- hardware exposure
- ZFS-backed persistence

The host should stay as lean as possible. Heavy user-facing AI services should not run directly on the Proxmox host.

### 2. Privileged LXC for AI workloads

The main AI container is responsible for:

- direct access to AMD GPU devices
- llama.cpp user-space runtime
- Docker runtime for application stacks
- mounted model storage

This design avoids full VM overhead while keeping a clean separation from the host.

### 3. Docker application stacks

Docker inside the AI LXC is used for services such as:

- ComfyUI
- OpenWebUI
- automation and orchestration tools
- vector search or retrieval helpers
- media-related support services

## Why This Design

- near-bare-metal GPU access inside LXC
- simpler storage sharing through mounted directories
- clear persistence boundaries
- easier service lifecycle management through compose stacks
- less overhead than a dedicated GPU VM

## Trade-Offs

- privileged LXC is not the same security boundary as a VM
- GPU kernel-space drivers remain host-managed
- ROCm-enabled setups can still be fragile and version-sensitive
- Docker plus LXC is operationally convenient, but not minimal

## Current Bias

The current operating bias of the reference stack is:

- llama.cpp close to the metal in the LXC
- Docker for application services
- shared model storage
- a clear split between LLM and diffusion assets

See also:

- [service-boundaries.md](service-boundaries.md)
- [lxc-layout.md](lxc-layout.md)
- [storage-layout.md](storage-layout.md)
