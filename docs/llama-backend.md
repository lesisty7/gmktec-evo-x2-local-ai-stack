# llama.cpp Backend

## Purpose

The LLM backend is based on `llama.cpp` running directly inside the main AI LXC rather than inside a Docker container.

This keeps the serving path closer to the hardware while still allowing the rest of the stack to stay containerized.

## Current Operating Model

The current design uses:

- `llama-server`
- router mode
- a managed environment file
- a managed model preset file
- a systemd service for lifecycle control

Key configuration concepts:

- `router.env`
- `models.ini`
- a small management script

In the reference setup, the operator-managed destination for `router.env` and `models.ini` is:

- `/etc/llama/router.env`
- `/etc/llama/models.ini`

Public-safe examples are included here:

- [../examples/llama/router.env.example](../examples/llama/router.env.example)
- [../examples/llama/models.ini.example](../examples/llama/models.ini.example)
- [../examples/llama/README.md](../examples/llama/README.md)
- [../scripts/llama/update-llama.sh](../scripts/llama/update-llama.sh)

## Required Directories

The reference layout expects these paths to exist before the backend is fully useful:

- `/etc/llama`
- `/opt/llama.cpp`
- `/mnt/ai-models/llm`
- `/mnt/ai-models/cache/llama.cpp`
- `/mnt/ai-models/cache/hf`

These are not arbitrary details. They express the basic split between:

- operator-owned config
- checked-out source and built binaries
- model assets
- reusable cache data

## What The User Must Do

This repository does not ship models.

A user starting from scratch must do both of these things:

1. download their own GGUF models into the expected model directory, typically `/mnt/ai-models/llm`
2. edit `models.ini` so the preset names, model paths, and routing choices match the models they actually installed

Without those two steps, the backend layout may exist, but the router configuration will not reflect the real local model inventory.

## Why Router Mode

Router mode makes it practical to:

- keep multiple model presets in one place
- switch between models without rebuilding the whole stack
- expose a cleaner serving interface to upstream tools
- support chat, embeddings, and multimodal presets in one backend

## Current Update and Build Procedure

The current reference stack uses a management script named `update-llama.sh`.

It should be run only inside the main Ubuntu LXC that hosts the AI runtime.

Do not run this script on the Proxmox host.

Its job is to manage:

- repository updates
- dependency installation
- compilation
- service mode selection
- protection of existing config files
- fast switching between scan modes without recompilation

A public-safe reference version of that script is included here:

- [../scripts/llama/update-llama.sh](../scripts/llama/update-llama.sh)

Treat it as a reference implementation tied to this architecture style, not as a universal drop-in script for every ROCm machine.

For publication clarity, the public file is named `update-llama.sh`, but its logic is intentionally kept aligned with the known-working local manager script rather than being heavily rewritten for style.

## Script Help

For convenience, the public draft includes the current CLI help here as well:

```text
Usage: update-llama.sh [OPTIONS] [VERSION]

Manages llama.cpp installation, compilation, dependencies, and systemd service.

Arguments:
  VERSION                    Tag, branch, or commit hash (default: master).
                             (Ignored if using --switch-to-* flags).

Update & Build Options:
  --scan-folder              Perform FULL BUILD and set mode to directory scanning.
                             This is the DEFAULT mode.
  --scan-ini                 Perform FULL BUILD and set mode to INI preset.
                             Requires /etc/llama/models.ini file.
  --no-deps                  Skip system dependency installation (apt-get).

Fast Switch Options (No Recompile):
  --switch-to-scan-folder    Quickly reconfigure service to Folder Mode WITHOUT compiling.
                             Fails if the binary does not exist.
  --switch-to-scan-ini       Quickly reconfigure service to INI Mode WITHOUT compiling.
                             Fails if the binary does not exist.

General Options:
  --check-only              Print status only (no changes).
  -h, --help                 Show this help message.
```

## Operational Modes

The script supports two main model discovery modes.

### Scan Folder Mode

Use this mode when the service should discover models directly from a models directory.

Typical use:

```bash
./update-llama.sh
./update-llama.sh --scan-folder
```

### INI Preset Mode

Use this mode when you want explicit model presets defined in `models.ini`.

Typical use:

```bash
./update-llama.sh --scan-ini
```

This mode requires a valid `models.ini` file.

## Fast Switches

The script also supports fast mode switching without recompilation.

Examples:

```bash
./update-llama.sh --switch-to-scan-folder
./update-llama.sh --switch-to-scan-ini
```

These are useful when:

- the binary already exists
- you only want to change service mode
- you do not want to rebuild `llama.cpp`

## Check-Only Mode

For a safe status check:

```bash
./update-llama.sh --check-only
```

This is useful to inspect state without changing files or systemd configuration.

## Version Selection

You can also target a specific tag, branch, or commit:

```bash
./update-llama.sh master
./update-llama.sh b4450
```

## Practical Recommendation

For public documentation, the safest way to explain this workflow is:

1. keep `router.env` and `models.ini` as operator-owned files
2. use the script to update and build
3. use fast switches only when the binary is already known-good
4. use `--check-only` before and after meaningful changes

## Memory Recycling Note

The reference stack also uses idle-based model shutdown through `sleep-idle-seconds` in `models.ini`.

See [memory-recycling.md](memory-recycling.md) for the practical pattern and trade-offs.

## What This Public Draft Does Not Include

This draft intentionally does not publish:

- private service units
- live hostnames or private endpoints
- production-specific model paths beyond illustrative examples
- any credentials or tokens related to the backend
