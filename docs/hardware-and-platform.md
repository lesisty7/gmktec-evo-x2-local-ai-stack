# Hardware and Platform

## Reference Hardware

- device family: `GMKtec Evo-X2`
- commercial variant used as reference: `EVO-X2 128 GB + 2 TB class`
- CPU: `AMD Ryzen AI Max+ 395`
- platform family: `Strix Halo`
- integrated GPU: `Radeon 8060S`
- GPU architecture identifier commonly seen in Linux tooling: `gfx1151`
- memory profile: `128 GB system RAM`

## Physical Starting Point

The reference machine was treated as a dedicated Linux and Proxmox box rather than as a dual-purpose Windows mini PC.

Important practical detail:

- the original Windows 11 SSD was removed
- the storage layout was rebuilt around two larger NVMe drives
- the system was then installed fresh with Proxmox VE on a mirrored ZFS layout

That choice matters because it changes the machine from an appliance-style mini PC into a purpose-built local AI host.

## Storage Starting Point

The reference setup uses:

- `2 x WD_BLACK SN7100 4 TB NVMe`
- mirrored ZFS on the Proxmox host
- separate mounted areas for models and persistent application data

The exact drive model is less important than the pattern:

- fast NVMe storage
- mirrored host storage for resilience
- clear split between model assets and service data

## Why This Matters for a From-Scratch Build

Someone starting from zero should understand that this stack is not documented as:

- a Windows-first setup
- a dual-boot gaming machine
- a generic desktop virtualization walkthrough

It is documented as a dedicated local AI machine with:

- Proxmox on bare metal
- a privileged Ubuntu LXC for the AI runtime
- Docker inside the LXC for higher-level services
- host-managed ZFS storage

## Platform Assumptions

- Proxmox VE on the host
- Ubuntu LXC for the main AI workload container
- AMD ROCm or HIP-capable user-space stack where relevant
- Docker available inside the AI LXC

## Memory and GPU Bias

This reference design assumes a large shared-memory AMD system rather than a classic discrete-GPU desktop.

Practical implications:

- the machine is expected to serve both LLM and diffusion workloads from one RAM-heavy platform
- Linux memory reporting for the GPU can look unusual compared to discrete VRAM-centric systems
- model selection and quantization policy matter more than chasing consumer-GPU assumptions

## Proxmox UI Reference Screenshots

The draft repo currently includes two Proxmox screenshots captured from the reference setup:

- [proxmox-network.png](images/proxmox-network.png)
- [proxmox-disks.png](images/proxmox-disks.png)

They are useful as visual references for the host configuration, but they must be reviewed manually before publication to ensure they do not expose private infrastructure details.

Use them as supporting visuals, not as the main source of truth. The written docs should still stand on their own after the screenshots are removed or replaced.

## Design Bias

This setup is optimized for:

- local-first inference
- high RAM availability
- shared model storage
- mixed LLM and diffusion usage

It is not primarily designed for:

- consumer desktop virtualization
- Windows GPU passthrough use cases
- multi-tenant hostile environments
