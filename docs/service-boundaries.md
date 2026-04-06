# Service Boundaries

This document explains where each major responsibility lives in the current design.

The exact implementation details may change over time, but the boundary model is one of the most reusable parts of the stack.

## Boundary Summary

### Proxmox host

The host is responsible for:

- booting and running the hypervisor
- managing ZFS storage
- exposing hardware devices to the LXC
- owning the container lifecycle

The host is intentionally kept lean. It should not become the place where user-facing AI services accumulate over time.

### Main AI LXC

The privileged Ubuntu LXC is the main runtime boundary for AI workloads.

It is responsible for:

- the Linux userspace used by AI services
- direct access to AMD GPU device nodes
- the `llama.cpp` runtime
- the Docker engine used by higher-level services
- mounted storage for models and persistent application data

This is the operational center of the stack.

### Docker inside the LXC

Docker is used for services that benefit from:

- isolated service packaging
- compose-based lifecycle management
- easier upgrades and restarts
- cleaner separation between user-facing apps

Examples include:

- ComfyUI
- OpenWebUI
- automation and orchestration tools
- search and vector services
- support services such as reverse proxy or media helpers

### Shared mounted storage

Mounted storage exists to keep important data outside ephemeral container filesystems.

In practice, the reference stack separates:

- model storage under `/mnt/ai-models`
- persistent app data under `/mnt/containers`
- compose definitions and helpers under `/opt/stacks`

## Why These Boundaries Work Well

- the host stays operationally simpler
- the LXC keeps AI runtimes close to the hardware
- Docker handles service packaging without owning the hardware boundary
- storage ownership is easier to reason about
- backups and migrations can be planned per dataset instead of per container image

## What This Design Is Not Optimizing For

- the strongest possible VM-style isolation
- the fewest possible moving parts
- turnkey portability across every environment

It is a pragmatic single-operator design, not a generic enterprise reference architecture.

## Practical Rule of Thumb

When deciding where something belongs:

- if it is hardware exposure or storage ownership, it probably belongs to the Proxmox host
- if it is a core AI runtime that benefits from staying close to the machine, it probably belongs in the LXC userspace
- if it is a user-facing application or helper service, it probably belongs in Docker inside the LXC

See also:

- [architecture.md](architecture.md)
- [lxc-layout.md](lxc-layout.md)
- [storage-layout.md](storage-layout.md)
- [stack-overview.md](stack-overview.md)
