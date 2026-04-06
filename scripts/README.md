# Scripts

This directory contains public-safe helper scripts that are useful enough to publish as part of the first release.

The goal is not to dump every local operational script. The goal is to keep only the scripts that help explain or reproduce the core architecture.

## Current Contents

### `llama/update-llama.sh`

A public-safe `llama.cpp` manager script for:

- cloning or updating `llama.cpp`
- building the HIP backend
- protecting operator-owned config files
- switching between folder scanning and INI preset mode
- updating the `systemd` service

Treat it as a reference implementation and adapt it to your own paths and packaging decisions.

In this draft, the public filename is simplified to `update-llama.sh`, but the script logic is intentionally kept very close to the working local source version so the published example stays operational.
