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
- a small management script plus a dedicated Vulkan wrapper

In the reference setup, the operator-managed destination for `router.env` and `models.ini` is:

- `/etc/llama/router.env`
- `/etc/llama/models.ini`

Public-safe examples are included here:

- [../examples/llama/router.env.example](../examples/llama/router.env.example)
- [../examples/llama/models.ini.example](../examples/llama/models.ini.example)
- [../examples/llama/README.md](../examples/llama/README.md)
- [../scripts/llama/update-llama.sh](../scripts/llama/update-llama.sh)
- [../scripts/llama/update-llama-vulkan.sh](../scripts/llama/update-llama-vulkan.sh)

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

In the reference setup, router mode is intentionally limited to one loaded model at a time.

That behavior is controlled in `router.env` through:

- `LLAMA_MODELS_MAX=1`

This keeps memory usage more predictable and fits the way the reference stack recycles idle models.

## Current Backend Status

As of `2026-04-08`, the documented reference setup defaults to `Vulkan` for `llama.cpp`.

That is a pragmatic choice, not a claim that Vulkan is universally better.

In the reference environment used to refresh this repository:

- `Vulkan` loaded and generated correctly on tested models
- `HIP/ROCm` remained available as a fallback path
- recent `HIP/ROCm` tests hit repeated child-process crashes during tensor loading in:
  `libhsa-runtime64.so.1.18.70101`

Because of that, the public script now defaults to Vulkan while still allowing explicit ROCm/HIP rebuilds when needed.

## Informal Vulkan Throughput Snapshot

The numbers below are not a rigorous benchmark suite. They are practical single-environment observations from the refreshed reference setup, useful mainly as a rough expectation check for the current `Vulkan` path.

Reference context:

- backend: `Vulkan`
- `llama.cpp`: `b8693`
- hardware family: `GMKtec Evo-X2`, `Ryzen AI Max+ 395`, `Radeon 8060S / gfx1151`
- measurements taken from real generation runs rather than from a dedicated synthetic bench harness

| Model | Quant | Generated tokens | Wall time | Approx. generation speed |
|---|---:|---:|---:|---:|
| `nvidia_Nemotron-3-Nano-30B-A3B` | `Q5_K_L` | `1632` | `26s` | `61.75 tok/s` |
| `gemma-4-26B-A4B-it` | `UD-Q5_K_XL` | `1820` | `39s` | `46.38 tok/s` |
| `Qwen3.5-35B-A3B` | `UD-Q6_K_XL` | `2260` | `52s` | `43.30 tok/s` |
| `GLM-4.7-Flash` | `UD-Q6_K_XL` | `1844` | `37s` | `48.76 tok/s` |
| `O-Researcher-72B-rl.i1` | `Q4_K_M` | `395` | `1m 26s` | `4.59 tok/s` |
| `Qwen3.5-27B` | `UD-Q6_K_XL` | `1382` | `2m 56s` | `7.84 tok/s` |
| `Qwen3.5-9B` | `UD-Q6_K_XL` | `1186` | `48s` | `24.35 tok/s` |

Treat these as a snapshot, not as a promise:

- prompt shape matters
- context length matters
- router settings matter
- future `llama.cpp`, Mesa, Vulkan, and kernel changes can move these numbers significantly

In practical use, the biggest problem with larger dense models that spend time "thinking" is often not raw tokens-per-second throughput.

The more noticeable issue is usually time to first output token.

That is the delay users feel before anything appears on screen, and for some models it matters more than the eventual steady-state `tok/s` number.

In the refreshed reference setup, models in the `gemma` A4B / `Nemotron` A3B family have felt especially good in practice because they combine strong usefulness with much better perceived responsiveness than some heavier alternatives.

Those families are also interesting because they sit in the more efficient sparse or hybrid-MoE-style part of the local model landscape rather than behaving like straightforward dense large models all the way through.

For `Nemotron-3-Nano-30B-A3B`, the practical target in this setup is not a tiny debug context but a genuinely large one. A working operating range around `250000` to `500000` tokens is a more representative target than low-context debugging presets.

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
- [../scripts/llama/update-llama-vulkan.sh](../scripts/llama/update-llama-vulkan.sh)

Treat it as a reference implementation tied to this architecture style, not as a universal drop-in script for every AMD machine.

`update-llama.sh` keeps the general operational flow of the older HIP/ROCm-first script, but now defaults to Vulkan for a currently working public-safe baseline. `update-llama-vulkan.sh` is just a thin wrapper that makes that default explicit.

## Script Help

For convenience, the public draft includes the current CLI help here as well:

```text
Usage: update-llama.sh [OPTIONS] [VERSION]

Manages llama.cpp installation, compilation, dependencies, and systemd service.

Arguments:
  VERSION                    Tag, branch, or commit hash (default: b8693).
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

Backend selection:
  Default backend is 'vulkan'.
  To force ROCm/HIP for a run:
    LLAMA_BACKEND=hip ./update-llama.sh --scan-ini
  Dedicated Vulkan wrapper:
    ./update-llama-vulkan.sh --scan-ini
```

## Operational Modes

The script supports two main model discovery modes.

### Scan Folder Mode

Use this mode when the service should discover models directly from a models directory.

Typical use:

```bash
./update-llama.sh
./update-llama.sh --scan-folder
./update-llama-vulkan.sh --scan-folder
```

### INI Preset Mode

Use this mode when you want explicit model presets defined in `models.ini`.

Typical use:

```bash
./update-llama.sh --scan-ini
./update-llama-vulkan.sh --scan-ini
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
LLAMA_BACKEND=hip ./update-llama.sh b4450
```

## Practical Recommendation

For public documentation, the safest way to explain this workflow is:

1. keep `router.env` and `models.ini` as operator-owned files
2. use the script to update and build
3. use fast switches only when the binary is already known-good
4. use `--check-only` before and after meaningful changes
5. treat Vulkan as the current known-good default, not as a permanent architectural rule

## Memory Recycling Note

The reference stack also uses idle-based model shutdown through `sleep-idle-seconds` in `models.ini`.

See [memory-recycling.md](memory-recycling.md) for the practical pattern and trade-offs.

## What This Public Draft Does Not Include

This draft intentionally does not publish:

- private service units
- live hostnames or private endpoints
- production-specific model paths beyond illustrative examples
- any credentials or tokens related to the backend
