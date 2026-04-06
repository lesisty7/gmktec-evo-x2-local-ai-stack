# Open WebUI Stack Example

This directory contains a public-safe example of the `openwebui` stack used by the reference project.

## What It Shows

- an Open WebUI container with persistent data
- a `pipelines` sidecar
- an Apache Tika sidecar for document extraction
- integration points for `llama.cpp`, ComfyUI, SearXNG, and speech services

## Included Files

- `.env.example`
- `docker-compose.example.yml`

## How to Use It

1. Copy `.env.example` to `.env`.
2. Adjust names, ports, paths, and base URLs for your environment.
3. Review which backends you actually want to expose.
4. Start the stack with Docker Compose.

## Important Notes

- This is a structural example, not a literal export from a live system.
- Backend URLs intentionally use example values and may point either to loopback, `host.docker.internal`, or other service containers depending on your own design.
- The published example keeps `OPENAI_API_KEY`-style values as placeholders because many OpenAI-compatible clients require a non-empty key even for local backends.

## Related Files

- [../../../docs/stack-overview.md](../../../docs/stack-overview.md)
- [../../../docs/service-boundaries.md](../../../docs/service-boundaries.md)
- [../media/README.md](../media/README.md)
- [../search/README.md](../search/README.md)
