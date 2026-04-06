# Security and Publication Guardrails

This repository is being prepared for future public release. Until a dedicated audit is complete, treat it as a private staging area.

## Hard Rules

- Do not publish this repository yet.
- Do not commit real `.env` files.
- Do not commit tokens, passwords, API keys, cookies, or OAuth material.
- Do not commit real IP addresses for private infrastructure unless they are explicitly approved for publication.
- Do not commit internal DNS names, reverse proxy targets, or personal hostnames unless they are sanitized.
- Do not commit production logs, generated outputs, database snapshots, or browser session state.
- Do not commit private backup files by default.

## Safe-to-Publish Categories

- architecture diagrams and written documentation
- hardware notes
- storage layout concepts
- sanitized example compose files
- sanitized example llama.cpp router presets
- public-safe model directory layouts
- benchmark methodology without private endpoints

## Sensitive Categories Requiring Review

- any `.env`-like file
- reverse proxy configuration
- compose files with real URLs or ports tied to a private network
- scripts that might embed repo URLs, tokens, or curl headers
- browser automation configs
- MCP configs
- anything with API keys, bearer tokens, or SSH hints

## Required Audit Before Publication

1. Search for secrets by pattern.
2. Search for private IP ranges.
3. Search for domain names and internal hostnames.
4. Search for bearer tokens, JWTs, and API keys.
5. Review all example files manually.
6. Review git history before first public push.

## Suggested Secret Search Patterns

Examples of what must be checked before publication:

- `192.168.`
- `10.`
- `172.16.`
- `172.17.`
- `172.18.`
- `172.19.`
- `172.2`
- `Authorization: Bearer`
- `API_KEY`
- `TOKEN`
- `PASSWORD`
- `SECRET`
- `PRIVATE`
- `ssh root@`

## Publication Gate

This repository may only be published after an explicit go-ahead following a security audit.

