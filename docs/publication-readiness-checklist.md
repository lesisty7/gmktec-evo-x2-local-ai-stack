# Publication Readiness Checklist

Use this checklist before the first public push.

## Secret Review

- remove all real `.env` files
- remove all tokens and API keys
- remove bearer headers and JWTs
- remove cookies and local auth state
- remove private SSH targets

## Network Redaction

- remove private IP addresses
- remove internal hostnames
- remove reverse proxy upstream targets
- remove local-only service URLs

## File Review

- review all compose files
- review all example configs
- review all shell scripts
- review all docs for accidental infrastructure leakage
- review repository history, not only the working tree

## Repo Hygiene

- remove backups that do not belong in the public repo
- remove generated smoke artifacts
- remove runtime logs
- remove local caches
- remove nested unrelated projects

## Final Gate

- security audit completed
- publication explicitly approved

