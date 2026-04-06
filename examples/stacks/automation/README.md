# Automation Stack Example

This directory contains a public-safe environment example derived from a real automation stack, but rewritten to remove private IPs, tokens, and service-specific URLs.

## What It Shows

- a typical `n8n` and database baseline
- a Docker Compose example for the stack
- browser automation related environment variables
- webhook and hostname shaping
- optional integration points for vector storage and chat systems
- a small `python-runner` sidecar used for script execution

## Included Files

- `.env.example`
- `docker-compose.example.yml`
- `python-runner/Dockerfile`
- `python-runner/app.py`

## How to Use It

- copy `.env.example` to `.env`
- replace every `replace_with_*` value
- replace the example internal hostnames with your own DNS or IP plan
- remove integrations you do not need

## Important Note

This is intentionally an example environment file, not a production export. It is meant to show shape and categories of settings, not exact working values for another installation.
