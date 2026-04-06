# Release Scope

This document defines what belongs in the first public release of this repository.

The goal is to keep the first version useful, coherent, and safe. It is better to publish a smaller high-quality repository than a larger repository full of local edge cases.

## Publish in the First Release

### Core documentation

- `README.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `LICENSE.md`
- `STATUS.md`
- `docs/from-scratch.md`
- `docs/architecture.md`
- `docs/stack-overview.md`
- `docs/service-boundaries.md`
- `docs/hardware-and-platform.md`
- `docs/lxc-layout.md`
- `docs/storage-layout.md`
- `docs/proxmox-zfs-helper.md`
- `docs/llama-backend.md`
- `docs/mcp-codex.md`
- `docs/mcp-comfyui.md`
- `docs/mcp-search.md`
- `docs/memory-recycling.md`
- `docs/model-layout.md`
- `docs/model-tree-snapshot.md`
- `docs/faq.md`
- `docs/publication-readiness-checklist.md`
- `docs/screenshot-review.md`

### Example files

- `examples/llama/README.md`
- `examples/llama/models.ini.example`
- `examples/llama/router.env.example`
- `examples/mcp/README.md`
- `examples/mcp/comfyui.env.example`
- `examples/mcp/searxng.env.example`
- `examples/stacks/automation/.env.example`
- `examples/stacks/mcp-playwright/.env.example`
- `examples/stacks/media/.env.example`
- `examples/stacks/media/docker-compose.example.yml`
- `examples/stacks/qdrant/.env.example`
- `examples/stacks/rocketchat/.env.example`
- `examples/stacks/mattermost/.env.example`
- the corresponding example `README.md` files

### Public-safe scripts

- `scripts/README.md`
- `scripts/llama/update-llama.sh`
- `scripts/mcp/comfyui_mcp_v1.py`
- `scripts/mcp/comfyui_mcp_v2.py`
- `scripts/mcp/searxng_mcp.py`

### Images

- `docs/images/proxmox-network.png`
- `docs/images/proxmox-disks.png`

These are acceptable only if they still pass the final manual review at publication time.

## Probably Publish Later

These are good candidates for a later iteration rather than for the first release:

- additional diagrams beyond the existing Mermaid architecture diagram
- more stack examples, but only if they are clearly useful and not too environment-specific
- benchmarking notes
- service-specific troubleshooting documents
- a separate document for update workflows across the whole stack

## Do Not Publish in the First Release

- raw production `.env` files
- reverse proxy rules from the live environment
- host-specific operational backups
- browser sessions or auth state
- firmware artifacts of unclear origin or licensing status
- misdownloaded files such as HTML pages saved with binary-looking extensions
- local-only service experiments that do not improve the public story
- Samba-specific local details unless they are rewritten into a genuinely reusable example

## Scope Principle

The first release should communicate a clear story:

1. what the machine is
2. why Proxmox plus privileged LXC was chosen
3. how storage is organized
4. how `llama.cpp` and ComfyUI fit into the design
5. how to think about examples safely

Anything that weakens that story should either be rewritten or left out of the first public version.
