#!/bin/sh
set -eu

QDRANT_URL=${QDRANT_URL:-http://qdrant:6333}
QDRANT_COLLECTION=${QDRANT_COLLECTION:-knowledge_base}
QDRANT_REMOTE_URL=${QDRANT_REMOTE_URL:-}

if [ -z "$QDRANT_REMOTE_URL" ]; then
  echo "QDRANT_REMOTE_URL is not set" >&2
  exit 1
fi

AUTH_HEADER=""
if [ -n "${QDRANT_API_KEY:-}" ]; then
  AUTH_HEADER="-H api-key:${QDRANT_API_KEY}"
fi

REMOTE_AUTH_HEADER=""
if [ -n "${QDRANT_REMOTE_API_KEY:-}" ]; then
  REMOTE_AUTH_HEADER="-H api-key:${QDRANT_REMOTE_API_KEY}"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SNAPSHOT_PATH="/backup/${QDRANT_COLLECTION}-${STAMP}.snapshot"

echo "Creating snapshot for ${QDRANT_COLLECTION}..."
RESP=$(curl -sS -X POST ${AUTH_HEADER} "${QDRANT_URL}/collections/${QDRANT_COLLECTION}/snapshots")
NAME=$(echo "$RESP" | jq -r '.result.name // empty')
if [ -z "$NAME" ]; then
  echo "Snapshot creation failed: $RESP" >&2
  exit 1
fi

echo "Downloading snapshot ${NAME}..."
curl -sS ${AUTH_HEADER} "${QDRANT_URL}/collections/${QDRANT_COLLECTION}/snapshots/${NAME}" -o "$SNAPSHOT_PATH"

if [ ! -s "$SNAPSHOT_PATH" ]; then
  echo "Snapshot download failed or empty: $SNAPSHOT_PATH" >&2
  exit 1
fi

echo "Uploading snapshot to remote ${QDRANT_REMOTE_URL}..."
curl -sS -X POST ${REMOTE_AUTH_HEADER} \
  -F "snapshot=@${SNAPSHOT_PATH}" \
  "${QDRANT_REMOTE_URL}/collections/${QDRANT_COLLECTION}/snapshots/upload"

echo "Done: ${SNAPSHOT_PATH}"
