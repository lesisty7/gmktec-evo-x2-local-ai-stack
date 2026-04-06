# Proxmox ZFS Helper

Small public-safe helper for preparing storage on a Proxmox host for an LXC-based local AI stack.

This document is a short curated reference with practical commands for inspecting pools, creating datasets, and applying baseline settings for a local AI stack.

## What This Helper Covers

- checking ZFS pool state
- creating datasets for models and container data
- applying practical baseline ZFS settings
- basic verification steps

## Before You Start

- make sure you understand your pool and dataset names
- do not paste commands blindly into a production host
- review mountpoints before creating datasets
- use your own pool name instead of assuming `rpool`

## Basic Inspection

Useful read-only commands:

```bash
zpool list
zpool status
zfs list
mount | grep -E '/mnt|zfs'
ls -la /mnt
zpool get autotrim rpool
```

## Create a Dataset for Shared AI Models

Example:

```bash
zfs create -o mountpoint=/mnt/ai-models rpool/ai-models
```

Practical baseline settings for large model files:

```bash
zfs set atime=off rpool/ai-models
zfs set compression=off rpool/ai-models
zfs set recordsize=1M rpool/ai-models
zfs set logbias=throughput rpool/ai-models
zfs set xattr=sa rpool/ai-models
zfs set acltype=off rpool/ai-models
zfs set dedup=off rpool/ai-models
zfs set copies=1 rpool/ai-models
zfs set primarycache=all rpool/ai-models
```

Optional and risky:

```bash
# Consider only if you accept a higher risk of data loss after power failure.
# zfs set sync=disabled rpool/ai-models
```

Suggested subdatasets:

```bash
zfs create rpool/ai-models/llm
zfs create rpool/ai-models/sd
```

## Create a Dataset for Container Data

Example:

```bash
zfs create -o mountpoint=/mnt/containers -o atime=off -o compression=lz4 rpool/containers
```

Practical baseline settings for application data:

```bash
zfs set recordsize=16K rpool/containers
zfs set xattr=sa rpool/containers
zfs set acltype=posixacl rpool/containers
zfs set primarycache=all rpool/containers
zfs set dedup=off rpool/containers
zfs set copies=1 rpool/containers
```

Suggested service subdatasets:

```bash
zfs create rpool/containers/qdrant-data
zfs create rpool/containers/n8n-data
zfs create rpool/containers/dify-data
zfs create rpool/containers/llm-config
zfs create rpool/containers/comfyui-data
```

## Verification Commands

After creating datasets:

```bash
zfs list -r rpool/ai-models
zfs list -r rpool/containers
ls -ld /mnt/ai-models /mnt/ai-models/*
ls -ld /mnt/containers /mnt/containers/*
```

## Practical Notes

- `compression=off` can make sense for already-compressed large binaries such as GGUF and many model files
- `compression=lz4` is usually a reasonable default for container and app data
- `recordsize=1M` is a practical choice for large sequential model files
- `recordsize=16K` is a more typical application-data choice than `1M`
- `dedup=off` is the safe baseline unless you have a very specific reason and enough RAM for dedup
- `atime=off` is one of the simplest useful SSD-friendly settings because it avoids pointless access-time writes

## SSD Longevity Comment

For SSD-backed homelab systems, the biggest win is often not exotic optimization but avoiding unnecessary writes.

Examples of settings that help reduce noise and wear:

- `atime=off`
- avoiding unnecessary compression on already-compressed model blobs
- keeping dedup disabled unless you truly need it

That does not magically "save" an SSD on its own, but it is a sensible baseline for storage that serves very large model files and lots of repeated reads.

## LXC Template Discovery

Example:

```bash
pveam list local | grep ubuntu-24.04
```

Use this only as a discovery command. Available template names depend on your configured Proxmox storage.

## Minimal End-to-End Example

```bash
zpool status
zfs create -o mountpoint=/mnt/ai-models rpool/ai-models
zfs create rpool/ai-models/llm
zfs create rpool/ai-models/sd
zfs set atime=off rpool/ai-models
zfs set compression=off rpool/ai-models
zfs set recordsize=1M rpool/ai-models

zfs create -o mountpoint=/mnt/containers -o atime=off -o compression=lz4 rpool/containers
zfs set recordsize=16K rpool/containers
zfs set xattr=sa rpool/containers
zfs set acltype=posixacl rpool/containers
zfs create rpool/containers/comfyui-data

zfs list -r rpool/ai-models
zfs list -r rpool/containers
```
