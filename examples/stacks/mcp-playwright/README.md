# MCP Playwright Example

This directory contains a small public-safe environment example for an MCP Playwright service.

## Current Recommendation

This example reflects an older working pattern from the reference stack.

Today, I would usually recommend looking at:

- `https://github.com/microsoft/playwright-cli`

before adopting this stack shape for a new deployment.

In other words:

- this example is still useful as a reference
- but it should be treated as a more legacy or transitional pattern than the preferred long-term direction

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
