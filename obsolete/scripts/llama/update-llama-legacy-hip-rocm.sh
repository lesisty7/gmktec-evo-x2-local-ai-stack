#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GMKtec Evo-X2: Professional llama.cpp Manager (HIP/ROCm)
# Features: Build, Versioning, Mode Switching (Folder/INI), Config Protection
#           Fast Mode Switching (No Recompile), Dependency Management
# =============================================================================

# --- 1. Default Configuration and Constants ---

# Default operation mode (change to "ini" if you want it default without flags)
DEFAULT_MODE="scan-folder"

# System directories
LLAMA_CONFIG_DIR="/etc/llama"
LLAMA_DIR="/opt/llama.cpp"
REPO_URL="https://github.com/ggml-org/llama.cpp.git"

# Configuration file paths
ENV_FILE="${LLAMA_CONFIG_DIR}/router.env"
INI_FILE="${LLAMA_CONFIG_DIR}/models.ini"
UNIT_NAME="llama-router.service"

# Model and cache paths
MODELS_DIR="/mnt/ai-models/llm"
LLAMA_CACHE_DIR="/mnt/ai-models/cache/llama.cpp"
HF_CACHE_DIR="/mnt/ai-models/cache/hf"

# ROCm / Hardware settings (AMD Ryzen AI Max+ 395)
ROCM_PATH="/opt/rocm"
HIP_PATH="/opt/rocm"
HSA_OVERRIDE_GFX_VERSION="11.0.1"
ROCR_VISIBLE_DEVICES="0"

# Build settings
BUILD_DIR="build-hip"
CMAKE_BUILD_TYPE="Release"

# Internal flags
SKIP_BUILD=0
INSTALL_DEPS=1
TARGET_VERSION="master"
RUN_MODE="${DEFAULT_MODE}"
CHECK_ONLY=0

# Status variables for final report
STATUS_DEPS="Skipped"
STATUS_REPO_UPDATE="Skipped"
STATUS_BUILD="Skipped"
STATUS_INI="Existing (Preserved)"
STATUS_ENV="Existing (Preserved)"
STATUS_UNIT="Updated"
CURRENT_MODE=""

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

log() { printf '\033[1;34m[%s]\033[0m %s\n' "$(date -Is)" "$*" >&2; }
success() { printf '\033[1;32m[%s] SUCCESS: %s\033[0m\n' "$(date -Is)" "$*" >&2; }
warn() { printf '\033[1;33m[%s] WARN: %s\033[0m\n' "$(date -Is)" "$*" >&2; }
die() { printf '\033[1;31m[%s] ERROR: %s\033[0m\n' "$(date -Is)" "$*" >&2; exit 1; }

require_root() {
  [[ "${EUID}" -eq 0 ]] || die "This script must be run as root."
}

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "Missing critical command: $1"
}

show_help() {
  cat << EOF
Usage: $(basename "$0") [OPTIONS] [VERSION]

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

Configuration file behavior:
  The script CHECKS for the existence of /etc/llama/models.ini and router.env.
  If files exist, they are NOT overwritten (preserving your changes).
  If files are missing, they will be created from default templates.
  --check-only never modifies files or systemd state.

Examples:
  $(basename "$0")                          # Full update to master + build + folder mode
  $(basename "$0") --scan-ini               # Full update to master + build + INI mode
  $(basename "$0") b4450                    # Full downgrade to b4450 + build
  $(basename "$0") --switch-to-scan-ini     # FAST switch to INI mode (no build)
  $(basename "$0") --check-only             # Print status and exit
EOF
}

ensure_dirs() {
  log "Verifying directory structure..."
  mkdir -p "${LLAMA_CONFIG_DIR}"
  mkdir -p "${LLAMA_CACHE_DIR}"
  mkdir -p "${HF_CACHE_DIR}"

  if [[ ! -d "${MODELS_DIR}" ]]; then
     die "Models directory ${MODELS_DIR} does not exist. Check ZFS/Bind mounts."
  fi
}

# -----------------------------------------------------------------------------
# Dependency Management (Restored from old version)
# -----------------------------------------------------------------------------

install_dependencies() {
  if [[ "${INSTALL_DEPS}" -eq 0 ]]; then
    log "Skipping dependency installation (--no-deps)."
    STATUS_DEPS="Skipped (User Request)"
    return 0
  fi

  log "Checking and installing build dependencies..."

  # Ensure apt-get exists (Debian/Ubuntu based)
  if ! command -v apt-get &> /dev/null; then
    warn "apt-get not found. Skipping dependency installation (non-Debian system?)."
    STATUS_DEPS="Skipped (Not Debian)"
    return 0
  fi

  export DEBIAN_FRONTEND=noninteractive

  # Updating package lists
  apt-get update -y

# Installing required packages:
  # - build tools (git, cmake, gcc, pkg-config)
  # - libraries (curl, ssl)
  # - python (for scripts)
  # - Vulkan (omitted in HIP build, uncomment if needed for other apps)
  apt-get install -y \
    git ca-certificates curl \
    cmake build-essential pkg-config \
    libcurl4-openssl-dev libssl-dev \
    python3 python3-venv python3-pip \
    # libvulkan-dev mesa-vulkan-drivers glslc vulkan-tools

  STATUS_DEPS="Installed/Verified"
  success "Dependencies verified."
}

# -----------------------------------------------------------------------------
# Argument Parsing
# -----------------------------------------------------------------------------

# Simple argument parser
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    --no-deps)
      INSTALL_DEPS=0
      shift
      ;;
    --check-only)
      CHECK_ONLY=1
      INSTALL_DEPS=0
      SKIP_BUILD=1
      shift
      ;;
    --scan-folder)
      RUN_MODE="scan-folder"
      SKIP_BUILD=0
      shift
      ;;
    --scan-ini)
      RUN_MODE="scan-ini"
      SKIP_BUILD=0
      shift
      ;;
    --switch-to-scan-folder)
      RUN_MODE="scan-folder"
      SKIP_BUILD=1
      INSTALL_DEPS=0 # Usually no need to install deps if just switching config
      shift
      ;;
    --switch-to-scan-ini)
      RUN_MODE="scan-ini"
      SKIP_BUILD=1
      INSTALL_DEPS=0
      shift
      ;;
    -*)
      die "Unknown option: $1. Use --help."
      ;;
    *)
      TARGET_VERSION="$1"
      shift
      ;;
  esac
done

CURRENT_MODE="${RUN_MODE}"

# -----------------------------------------------------------------------------
# Service and Build Logic
# -----------------------------------------------------------------------------

stop_service() {
  log "Checking status of service ${UNIT_NAME}..."
  if systemctl is-active --quiet "${UNIT_NAME}"; then
    log "Stopping service ${UNIT_NAME} before update..."
    systemctl stop "${UNIT_NAME}" || die "Failed to stop service."
  else
    log "Service ${UNIT_NAME} is not running, continuing."
  fi
}

check_existing_binary() {
  local BIN_PATH="${LLAMA_DIR}/${BUILD_DIR}/bin/llama-server"
  if [[ ! -x "${BIN_PATH}" ]]; then
    die "Binary not found at ${BIN_PATH}. You cannot switch modes without a build. Run without --switch-to-* first."
  fi
  log "Binary found. Skipping compilation."
  STATUS_REPO_UPDATE="Skipped (Mode Switch)"
  STATUS_BUILD="Skipped (Mode Switch)"
}

prepare_repo() {
  STATUS_REPO_UPDATE="Updated to ${TARGET_VERSION}"
  if [[ ! -d "${LLAMA_DIR}/.git" ]]; then
    log "Cloning repository to ${LLAMA_DIR}..."
    mkdir -p "$(dirname "${LLAMA_DIR}")"
    git clone "${REPO_URL}" "${LLAMA_DIR}"
  fi

  cd "${LLAMA_DIR}"

  log "Fetching updates from remote..."
  git fetch --all --tags --force

  if [[ -n "$(git status --porcelain)" ]]; then
    warn "Repository has local changes. Executing git stash..."
    git stash
  fi

  log "Switching to version: ${TARGET_VERSION}..."
  git checkout "${TARGET_VERSION}" || die "Failed to switch to version ${TARGET_VERSION}."

  if git show-ref --verify --quiet "refs/heads/${TARGET_VERSION}"; then
    git pull --ff-only origin "${TARGET_VERSION}" || die "Git pull failed"
  fi

  git submodule update --init --recursive
  success "Repository ready: $(git rev-parse --short HEAD)"
}

clean_and_build() {
  STATUS_BUILD="Rebuilt (HIP)"
  cd "${LLAMA_DIR}"

  log "Cleaning build directory (${BUILD_DIR})..."
  rm -rf "${BUILD_DIR}"

  log "Configuring CMake (HIP/ROCm)..."
  export ROCM_PATH="${ROCM_PATH}"
  export HIP_PATH="${HIP_PATH}"

  cmake -B "${BUILD_DIR}" \
    -DGGML_HIP=ON \
    -DGGML_HIPBLAS=ON \
    -DAMDGPU_TARGETS="gfx1101" \
    -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
    -DCMAKE_PREFIX_PATH="${ROCM_PATH}"

  log "Compiling (Jobs: $(nproc))..."
  cmake --build "${BUILD_DIR}" --config Release -j"$(nproc)"

  if [[ ! -x "${LLAMA_DIR}/${BUILD_DIR}/bin/llama-server" ]]; then
    die "Compilation finished, but llama-server binary not found."
  fi
  success "Build finished successfully."
}

# -----------------------------------------------------------------------------
# Configuration Management (Protecting existing files)
# -----------------------------------------------------------------------------

ensure_ini_file() {
  # INI file is required ONLY in --scan-ini mode, but we check/create it
  # only if user requests it or if it doesn't exist but is needed.

  if [[ -f "${INI_FILE}" ]]; then
    log "INI file exists: ${INI_FILE}. NOT modifying it."
    STATUS_INI="Existing (Preserved)"
    return 0
  fi

  # Following the "do not touch" rule, we create it only if missing.
  log "Missing INI file. Creating new template: ${INI_FILE}..."
  STATUS_INI="Created New"

  cat >"${INI_FILE}" <<INIEOF
# /etc/llama/models.ini
# llama.cpp llama-server — Router Mode model presets (INI)
# Created by update script on $(date -Is)

# -----------------------------------------------------------------------------
# "Default" preset
# -----------------------------------------------------------------------------
[default]
ctx-size = 16196
n-gpu-layers = 999
warmup = 0
# sleep-idle-seconds = 3600

# -----------------------------------------------------------------------------
# Local GGUF models
# -----------------------------------------------------------------------------

[O-Researcher-72B-rl.i1-Q4_K_M]
model = ${MODELS_DIR}/O-Researcher-72B-rl.i1-Q4_K_M.gguf
ctx-size = 16196
n-gpu-layers = 999
warmup = 0

[nvidia_Nemotron-3-Nano-30B-A3B-Q5_K_L]
model = ${MODELS_DIR}/nvidia_Nemotron-3-Nano-30B-A3B-Q5_K_L.gguf
ctx-size = 16196
n-gpu-layers = 999
warmup = 0

[allura-forge_Llama-3.3-8B-Instruct-Q6_K_L]
model = ${MODELS_DIR}/allura-forge_Llama-3.3-8B-Instruct-Q6_K_L.gguf
ctx-size = 16196
n-gpu-layers = 999
warmup = 0

[zai-org_GLM-4.6V-Flash-Q6_K]
model = ${MODELS_DIR}/zai-org_GLM-4.6V-Flash-Q6_K.gguf
ctx-size = 16196
n-gpu-layers = 999
warmup = 0

[tinyllama-1.1b-chat-v1.0.Q4_0]
model = ${MODELS_DIR}/tinyllama-1.1b-chat-v1.0.Q4_0.gguf
ctx-size = 2048
n-gpu-layers = 999
warmup = 0

[Qwen3-VL-30B-A3B-Instruct-Q4_K_M]
model  = ${MODELS_DIR}/Qwen3-VL-30B-A3B-Instruct-Q4_K_M/model.gguf
mmproj = ${MODELS_DIR}/Qwen3-VL-30B-A3B-Instruct-Q4_K_M/mmproj.gguf
ctx-size = 16196
n-gpu-layers = 999
warmup = 0

[nomic-embed-text-v1.5.Q4_K_M]
model = ${MODELS_DIR}/nomic-embed-text-v1.5.Q4_K_M.gguf
embeddings = 1
ctx-size = 8192
n-gpu-layers = 999
warmup = 0
INIEOF

  chmod 0644 "${INI_FILE}"
}

ensure_env_file() {
  local BIN_PATH="${LLAMA_DIR}/${BUILD_DIR}/bin/llama-server"

  if [[ -f "${ENV_FILE}" ]]; then
    log "ENV file exists: ${ENV_FILE}. NOT modifying it."
    STATUS_ENV="Existing (Preserved)"
    return 0
  fi

  log "Missing ENV file. Creating new: ${ENV_FILE}..."
  STATUS_ENV="Created New"

  cat >"${ENV_FILE}" <<ENVEOF
# Generated by update-llama-legacy-hip-rocm.sh on $(date -Is)
# Version: ${TARGET_VERSION}

# Hardware / ROCm
ROCM_PATH=${ROCM_PATH}
HIP_PATH=${HIP_PATH}
HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION}
ROCR_VISIBLE_DEVICES=${ROCR_VISIBLE_DEVICES}
# Fix library paths for ROCm
LD_LIBRARY_PATH=${ROCM_PATH}/lib:\${LD_LIBRARY_PATH}
PATH=${ROCM_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Caches
LLAMA_CACHE=${LLAMA_CACHE_DIR}
HF_HOME=${HF_CACHE_DIR}
HUGGINGFACE_HUB_CACHE=${HF_CACHE_DIR}/hub
TRANSFORMERS_CACHE=${HF_CACHE_DIR}/transformers

# Router Configuration
LLAMA_HOST=0.0.0.0
LLAMA_PORT=11434
LLAMA_MODELS_DIR=${MODELS_DIR}
LLAMA_MODELS_MAX=1
LLAMA_CTX=32392
LLAMA_NGL=999

# Binary
LLAMA_SERVER_BIN=${BIN_PATH}
ENVEOF
  chmod 0644 "${ENV_FILE}"
}

# -----------------------------------------------------------------------------
# Check-only status (no changes)
# -----------------------------------------------------------------------------

check_only_report() {
  local BIN_PATH="${LLAMA_DIR}/${BUILD_DIR}/bin/llama-server"
  local UNIT_PATH="/etc/systemd/system/${UNIT_NAME}"
  local bin_status="missing"
  local env_status="missing"
  local ini_status="missing"
  local unit_status="missing"
  local service_mode="unknown"
  local service_active="not-installed"
  local service_enabled="not-installed"

  if [[ -x "${BIN_PATH}" ]]; then
    bin_status="present"
  fi
  if [[ -f "${ENV_FILE}" ]]; then
    env_status="present"
  fi
  if [[ -f "${INI_FILE}" ]]; then
    ini_status="present"
  fi
  if [[ -f "${UNIT_PATH}" ]]; then
    unit_status="present"
    if grep -q -- "--models-preset" "${UNIT_PATH}"; then
      service_mode="scan-ini"
    elif grep -q -- "--models-dir" "${UNIT_PATH}"; then
      service_mode="scan-folder"
    fi
  fi

  if command -v systemctl >/dev/null 2>&1 && [[ "${unit_status}" == "present" ]]; then
    service_active="$(systemctl is-active "${UNIT_NAME}" 2>/dev/null || true)"
    service_enabled="$(systemctl is-enabled "${UNIT_NAME}" 2>/dev/null || true)"
  fi

  echo ""
  echo "========================================================"
  echo "   CHECK ONLY: GMKtec Evo-X2 llama.cpp"
  echo "========================================================"
  echo " Binary       : ${bin_status} (${BIN_PATH})"
  echo " ENV file     : ${env_status} (${ENV_FILE})"
  echo " INI file     : ${ini_status} (${INI_FILE})"
  echo " Systemd unit : ${unit_status} (${UNIT_PATH})"
  echo " Service mode : ${service_mode}"
  echo " Service      : active=${service_active} enabled=${service_enabled}"
  echo "========================================================"
}

# -----------------------------------------------------------------------------
# Systemd Generation (Dynamic based on mode)
# -----------------------------------------------------------------------------

manage_systemd_unit() {
  local UNIT_PATH="/etc/systemd/system/${UNIT_NAME}"
  local TEMP_UNIT=$(mktemp)
  local EXEC_START_CMD=""

  # Building ExecStart command based on mode
  if [[ "${RUN_MODE}" == "scan-ini" ]]; then
    # INI Mode: uses --models-preset
    log "Systemd configuration for mode: INI PRESET"
    EXEC_START_CMD='exec "$LLAMA_SERVER_BIN" \
  --host "$LLAMA_HOST" \
  --port "$LLAMA_PORT" \
  --models-preset /etc/llama/models.ini \
  --models-max "$LLAMA_MODELS_MAX" \
  --no-warmup'
  else
    # Folder Mode: uses --models-dir
    log "Systemd configuration for mode: FOLDER SCAN"
    EXEC_START_CMD='exec "$LLAMA_SERVER_BIN" \
  --host "$LLAMA_HOST" \
  --port "$LLAMA_PORT" \
  --models-dir "$LLAMA_MODELS_DIR" \
  --models-max "$LLAMA_MODELS_MAX" \
  -c "$LLAMA_CTX" \
  -ngl "$LLAMA_NGL" \
  --no-warmup'
  fi

  cat >"${TEMP_UNIT}" <<UNITEOF
[Unit]
Description=llama.cpp llama-server (Mode: ${RUN_MODE} | Ver: ${TARGET_VERSION})
After=network-online.target
Wants=network-online.target
RequiresMountsFor=${MODELS_DIR} ${LLAMA_CACHE_DIR} ${HF_CACHE_DIR}

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${LLAMA_DIR}
EnvironmentFile=${ENV_FILE}
Environment=HOME=/root

# Pre-flight checks
ExecStartPre=/usr/bin/test -x \${LLAMA_SERVER_BIN}
# Check config file based on mode
$( [[ "${RUN_MODE}" == "scan-ini" ]] && echo "ExecStartPre=/usr/bin/test -f /etc/llama/models.ini" || echo "ExecStartPre=/usr/bin/test -d \${LLAMA_MODELS_DIR}" )

# Router mode execution
ExecStart=/usr/bin/bash -lc '${EXEC_START_CMD}'

Restart=on-failure
RestartSec=5
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
UNITEOF

  if cmp -s "${UNIT_PATH}" "${TEMP_UNIT}"; then
    log "Systemd service file (${UNIT_PATH}) - NO CHANGES."
    STATUS_UNIT="No Change"
    rm "${TEMP_UNIT}"
  else
    mv "${TEMP_UNIT}" "${UNIT_PATH}"
    warn "Systemd service file (${UNIT_PATH}) - UPDATED (Mode: ${RUN_MODE})."
    STATUS_UNIT="Updated (Mode: ${RUN_MODE})"
    systemctl daemon-reload
  fi
}

finish_and_restart() {
  log "Starting service ${UNIT_NAME}..."
  systemctl enable "${UNIT_NAME}" >/dev/null
  systemctl restart "${UNIT_NAME}"

  sleep 2
  if systemctl is-active --quiet "${UNIT_NAME}"; then
    success "Service is running correctly."
    log "Logs: journalctl -u ${UNIT_NAME} -f"
  else
    die "Service failed to start. Check 'systemctl status ${UNIT_NAME}'"
  fi

  # Final summary
  echo ""
  echo "========================================================"
  echo "   UPDATE COMPLETE: GMKtec Evo-X2 AI Stack"
  echo "========================================================"
  echo " Target Version : ${TARGET_VERSION}"
  echo " Active Mode    : ${CURRENT_MODE}"
  echo "--------------------------------------------------------"
  echo " Dependencies   : ${STATUS_DEPS}"
  echo " Repo Status    : ${STATUS_REPO_UPDATE}"
  echo " Build Status   : ${STATUS_BUILD}"
  echo " INI Config     : ${STATUS_INI} (Path: ${INI_FILE})"
  echo " ENV Config     : ${STATUS_ENV} (Path: ${ENV_FILE})"
  echo " Systemd Unit   : ${STATUS_UNIT}"
  echo "========================================================"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
  log ">>> Starting llama.cpp update [Mode: ${RUN_MODE}] <<<"

  if [[ "${CHECK_ONLY}" -eq 1 ]]; then
    if [[ "${EUID}" -ne 0 ]]; then
      warn "Running --check-only without root. Some checks may be incomplete."
    fi
    check_only_report
    return 0
  fi

  require_root
  ensure_dirs

  # Config file logic (ensure everything is present before stopping service)
  ensure_ini_file
  ensure_env_file

  stop_service

  if [[ "${SKIP_BUILD}" == "1" ]]; then
    # FAST SWITCH MODE: Verify binary, skip build/repo
    check_existing_binary
  else
    # FULL UPDATE MODE: Install deps, update repo and recompile
    install_dependencies
    prepare_repo
    clean_and_build
  fi

  manage_systemd_unit
  finish_and_restart
}

main "$@"
