# LXC Examples

This directory contains public-safe example material related to the main AI LXC.

The goal is not to publish a raw `pct config` dump. The goal is to show the parts
that matter for a similar deployment:

- privileged Ubuntu LXC
- Docker-in-LXC
- GPU device exposure
- bind mounts for models and persistent app data
- a large-memory runtime profile

## Files

- `pct-config-main-lxc.example.conf`

## Important Note

This example is based on a real working container, but it is intentionally sanitized.

You must adapt:

- hostname
- IP address
- gateway
- MAC address
- storage names
- bind mounts
- CPU and RAM allocation

to your own Proxmox host and your own LAN.
