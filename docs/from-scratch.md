# From Scratch Setup

This document captures the high-value starting assumptions from the older internal notes, but aligns them with the current stack direction.

The goal is not to preserve every old command. The goal is to preserve the parts that still matter when building a similar machine from zero.

## Intended Starting Point

This reference build assumes:

- a `GMKtec Evo-X2`
- `AMD Ryzen AI Max+ 395`
- `Radeon 8060S`
- `128 GB RAM`
- the machine repurposed into a dedicated Proxmox host

In the reference build, the original Windows SSD was removed and the storage was rebuilt around mirrored NVMe drives with ZFS.

That choice matters because this is documented as a dedicated AI host, not as a stock Windows machine with AI tools layered on top.

It is also a deliberate storage-policy choice, not a claim that every similar machine must use two drives.

You can probably build a simpler version around one SSD if you do not want mirrored ZFS, but then you are intentionally choosing a different persistence and failure model than the reference setup.

## BIOS and Firmware Direction

Before installing the platform, the important baseline is:

- enable UEFI boot mode
- enable AMD virtualization support
- enable IOMMU / AMD-Vi / SVM related options

Exact BIOS naming varies by firmware version, so treat these as feature categories rather than exact menu labels.

## Host OS Direction

The documented host pattern is:

- Proxmox VE on bare metal
- ZFS-backed storage on the host
- a privileged Ubuntu LXC for the main AI runtime

This is intentionally not a Windows passthrough design.

## Storage Direction

The high-value storage ideas are:

- mirrored NVMe storage on the host
- ZFS for host-managed persistence
- a separate models tree
- separate persistent application datasets

Practical structure:

- `/mnt/ai-models/llm`
- `/mnt/ai-models/sd`
- `/mnt/ai-models/cache`
- `/mnt/containers/*`
- `/opt/stacks/*`

Important ZFS ideas worth keeping:

- enable `autotrim`
- use `atime=off`
- use different tuning for model storage and app data
- keep model storage and app data separate

See also:

- [hardware-and-platform.md](hardware-and-platform.md)
- [storage-layout.md](storage-layout.md)
- [proxmox-zfs-helper.md](proxmox-zfs-helper.md)

## GPU and IOMMU Direction

The reference design assumes:

- the host owns the AMD kernel driver stack
- the LXC gets direct access to `/dev/dri` and `/dev/kfd`
- the container uses host-managed GPU devices rather than PCI passthrough

Useful verification concepts on the host are:

- confirm `amdgpu` is active
- confirm IOMMU / AMD-Vi is enabled
- confirm `/dev/dri/card0`, `/dev/dri/renderD128`, and `/dev/kfd` exist

This is the meaningful part of the older guide. The exact command sequence can vary by kernel and Proxmox release.

## LXC Direction

The current design keeps the main AI runtime in one privileged Ubuntu LXC with:

- GPU device exposure
- mounted model storage
- mounted persistent service data
- Docker inside the LXC
- `llama.cpp` running directly in LXC userspace

That preserves the main benefits of the older approach:

- low overhead
- direct GPU access
- simple storage sharing
- one operational center for the AI stack

## What Changed Since the Older Notes

The biggest change is that the current stack should not be documented as a manual compile-and-wire process for every update.

The current direction is:

- use the management script for `llama.cpp`
- keep operator-owned config in `router.env` and `models.ini`
- use router mode instead of older single-model assumptions
- treat Docker stacks as curated service bundles rather than ad hoc containers

See:

- [llama-backend.md](llama-backend.md)
- [memory-recycling.md](memory-recycling.md)

## Important Non-Goal

This design does not try to give Windows VMs direct GPU access.

If you want a GPU-accelerated Windows VM, that is a different architecture and should be documented separately as a passthrough-first build.
