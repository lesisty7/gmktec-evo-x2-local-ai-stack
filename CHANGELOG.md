# Changelog

## 2026-04-08

### llama.cpp refresh

- refreshed the public `llama.cpp` management workflow
- updated the default public-safe backend to `Vulkan`
- kept `HIP/ROCm` available as an explicit fallback path via `LLAMA_BACKEND=hip`
- added `scripts/llama/update-llama-vulkan.sh` as a small wrapper for the current known-good path
- preserved the older HIP/ROCm-first public script under `obsolete/scripts/llama/update-llama-legacy-hip-rocm.sh`

### documentation refresh

- updated `README.md`, `docs/README.md`, and `docs/llama-backend.md`
- documented the currently isolated `ROCm/HSA` tensor-loading crash pattern seen in the refreshed reference environment
- clarified that the current Vulkan default is a practical snapshot, not a universal AMD recommendation
- updated the public `router.env.example` to reflect the current working path

### practical performance snapshot

- added an informal Vulkan throughput snapshot for several currently used models
- documented that the more important user-facing problem for larger "thinking" models is often time to first output token, not just steady-state `tok/s`
- noted that `gemma` A4B and `Nemotron` A3B style models have felt especially good in practice in the refreshed setup

### publication hygiene

- moved older public-safe files into `obsolete/` instead of deleting them
- rechecked the repository for accidental private infrastructure leftovers
- kept placeholder paths and example domains only where they are clearly documented as placeholders
