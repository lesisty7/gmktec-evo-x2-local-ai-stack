#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/data"
TARGET_DIR="${PROXY_DATA_ROOT:-/mnt/containers/proxy-data}"
CERT_DOMAIN="${1:-${BASE_DOMAIN:-ai.local}}"
CERT_ONLY=0

log() { printf '[%s] %s\n' "$(date -Is)" "$*"; }
warn() { printf '[%s] WARN: %s\n' "$(date -Is)" "$*"; }
die() { printf '[%s] ERROR: %s\n' "$(date -Is)" "$*" >&2; exit 1; }

show_help() {
  cat <<'USAGE'
Usage: pre-deploy.sh [options] [domain]

Options:
  --cert-only       Only (re)generate the self-signed certificate.
  -h, --help        Show this help message.

Arguments:
  domain            Certificate domain (default: BASE_DOMAIN or ai.local)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) show_help; exit 0 ;;
    --cert-only) CERT_ONLY=1; shift ;;
    *) CERT_DOMAIN="$1"; shift ;;
  esac
done

if [[ ! -d "${SOURCE_DIR}" ]]; then
  die "Missing source package: ${SOURCE_DIR}"
fi

mkdir -p "${TARGET_DIR}" "${TARGET_DIR}/certs"

if [[ "${CERT_ONLY}" -eq 0 ]]; then
  log "Preparing ${TARGET_DIR}"
  if [[ -z "${TARGET_DIR}" ]] || [[ "${TARGET_DIR}" == "/" ]]; then
    die "Refusing to clean root or empty path"
  fi
  rm -rf "${TARGET_DIR:?}"/*
  mkdir -p "${TARGET_DIR}/landing"
  cp -a "${SOURCE_DIR}/." "${TARGET_DIR}/"
fi

if command -v openssl >/dev/null 2>&1; then
  log "Generating self-signed certificate for ${CERT_DOMAIN}"
  openssl req -x509 -nodes -newkey rsa:4096 -days 3650 \
    -keyout "${TARGET_DIR}/certs/${CERT_DOMAIN}.key" \
    -out "${TARGET_DIR}/certs/${CERT_DOMAIN}.crt" \
    -subj "/CN=${CERT_DOMAIN}" \
    -addext "subjectAltName=DNS:${CERT_DOMAIN},DNS:*.${CERT_DOMAIN}"
else
  warn "openssl not found; skipping certificate generation"
fi

if [[ "${CERT_ONLY}" -eq 0 ]]; then
  log "Ready. Review nginx config and then run: docker compose up -d"
fi
