# Media Stack Example

This directory contains a public-safe example of the `media` stack shape used by the reference project.

## What It Shows

- a ComfyUI container for AMD hardware
- persistent model mounts
- persistent app data mounts
- a small idle-unloader sidecar
- a companion `.env.example` for paths, ports, and image tags

## What It Does Not Guarantee

- exact compatibility with your hardware
- exact compatibility with your ROCm stack
- exact compatibility with every custom node

## How to Use It

- copy `.env.example` to `.env`
- treat it as a structural example
- adapt paths to your own storage layout
- review image tags and environment variables for your own platform
- replace any environment-specific assumptions before real deployment

## Notes

- examples in this repository are intentionally conservative and documentation-oriented
- they should be reviewed before use in a live environment
- the reference stack also uses idle-based ComfyUI unloading; see [../../../docs/memory-recycling.md](../../../docs/memory-recycling.md)
