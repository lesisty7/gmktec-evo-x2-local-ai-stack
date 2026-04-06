# Proxy Stack Example

This directory contains a public-safe reverse-proxy example derived from the reference stack.

## What It Shows

- a small Nginx gateway container
- a landing page served directly by Nginx
- example subdomain routing for multiple internal AI services
- a helper script that prepares landing assets and self-signed certificates

## Included Files

- `.env.example`
- `docker-compose.example.yml`
- `pre-deploy.sh`
- `nginx/nginx.conf`
- `nginx/conf.d/ai.local.conf`
- `nginx/snippets/proxy-common.conf`
- `data/landing/index.html`

## Important Scope

This is intentionally a neutral starter package.

It does **not** try to reproduce the full private routing map of the live system.
Instead, it shows a clean pattern you can extend for your own domain and service set.

## How to Use It

1. Copy `.env.example` to `.env`.
2. Adjust the base domain and backend ports for your environment.
3. Run `./pre-deploy.sh your-domain.example` to prepare landing assets and self-signed certificates.
4. Review the generated Nginx package before exposing it outside your LAN.
5. Start the stack with Docker Compose.

## Related Files

- [../../../docs/service-boundaries.md](../../../docs/service-boundaries.md)
- [../openwebui/README.md](../openwebui/README.md)
- [../search/README.md](../search/README.md)
- [../media/README.md](../media/README.md)
