#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Dedicated wrapper for the currently working Vulkan setup.
# The main script keeps its original interface; this wrapper just makes the
# active backend explicit and repeatable.
export LLAMA_BACKEND="vulkan"

exec "${SCRIPT_DIR}/update-llama.sh" "$@"
