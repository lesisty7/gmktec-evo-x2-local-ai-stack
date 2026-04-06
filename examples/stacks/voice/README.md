# Voice Stack Example

This directory contains a public-safe example of the `voice` stack used by the reference project.

## What It Shows

- a compact `speaches` deployment for speech-to-text and text-to-speech
- model-related environment variables for Whisper and Piper
- a persistent cache directory for downloaded voice and speech assets

## Included Files

- `.env.example`
- `docker-compose.example.yml`

## How to Use It

1. Copy `.env.example` to `.env`.
2. Adjust model and voice choices for your own language and latency needs.
3. Adjust host paths and the Docker network name.
4. Start the stack with Docker Compose.

## Important Notes

- This example is CPU-oriented, matching the reference stack shape.
- Voice names and model names are examples and may not be available in every runtime or image version.
- Treat this as a practical starting point, not as a promise of perfect defaults for every language.
