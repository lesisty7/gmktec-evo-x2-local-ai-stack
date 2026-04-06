# Docling Stack Example

This directory contains a public-safe example of the `docling` stack used by the reference project.

## What It Shows

- a CPU-serving `docling` container
- container-safe threading and affinity settings
- a persistent cache directory for OCR and layout models

## Included Files

- `.env.example`
- `docker-compose.example.yml`

## Why It Matters

This stack is useful as a document extraction backend for higher-level tools such as Open WebUI or automation workflows.

## How to Use It

1. Copy `.env.example` to `.env`.
2. Adjust port binding, cache paths, and thread counts.
3. Start the stack with Docker Compose.

## Important Notes

- The affinity-related settings are there because CPU pinning assumptions can behave badly in containers.
- You should still validate thread counts for your own host and workload size.
