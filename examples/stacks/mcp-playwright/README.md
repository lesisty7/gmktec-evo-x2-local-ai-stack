# MCP Playwright Example

This directory contains a small public-safe environment example for an MCP Playwright service.

## What It Shows

- host and port binding
- a simple allowlist shape for upstream clients
- a Docker Compose example for the service
- an optional Dockerfile pattern for a debug-friendly wrapper image

## Included Files

- `.env.example`
- `docker-compose.example.yml`
- `Dockerfile`

## How to Use It

- copy `.env.example` to `.env`
- adjust port binding if needed
- review the allowed host list for your own network and tooling
- decide whether the plain compose image is enough or whether you need the more custom Dockerfile pattern
