# LXC Container Layout

This document summarizes the current structure of the main AI LXC used by the reference stack.

It is based on the actual Proxmox container configuration, but rewritten into a public-safe form.

## Runtime Shape

Current pattern:

- one main privileged Ubuntu LXC
- direct access to AMD GPU devices
- multiple bind mounts for shared model and app data
- Docker running inside the LXC

## Container-Level Resources

Representative shape of the current container:

- architecture: `amd64`
- CPU allocation: high-core-count profile
- RAM allocation: large-memory profile
- root filesystem on ZFS-backed local storage
- nesting enabled for Docker-in-LXC

## GPU Exposure

The container is configured with direct access to:

- `/dev/dri/card0`
- `/dev/dri/renderD128`
- `/dev/kfd`

That allows the LXC to use the host-managed AMD stack while keeping the actual workloads inside the container.

## Mount Layout

The current reference stack uses bind mounts for:

### Shared model storage

- `/mnt/ai-models/llm`
- `/mnt/ai-models/sd`
- `/mnt/ai-models/cache`

### Application data

- `/mnt/containers/open-webui-data`
- `/mnt/containers/postgres-data`
- `/mnt/containers/n8n-data`
- `/mnt/containers/qdrant-data`
- `/mnt/containers/dify-data`
- `/mnt/containers/comfyui-data`
- `/mnt/containers/llm-config`
- `/mnt/containers/searxng-data`
- `/mnt/containers/docling-data`
- `/mnt/containers/pipelines-data`
- `/mnt/containers/speaches-data`
- `/mnt/containers/docs-store`

## Design Comment

This mount layout is arguably a bit overkill.

It gives:

- strong separation between service data
- simpler backup targeting
- easier migration of individual services
- clearer storage ownership

But it also adds:

- more mount bookkeeping
- more dataset management overhead
- more documentation burden

For a homelab or single-operator system, fewer mounts can be perfectly reasonable.

## Practical Takeaway

The exact number of mounts matters less than the storage policy behind them.

What tends to matter more is:

- keeping model storage separate from app data
- keeping persistent data outside ephemeral container filesystems
- using sensible ZFS settings for SSD-backed workloads
- documenting what each mount is responsible for
