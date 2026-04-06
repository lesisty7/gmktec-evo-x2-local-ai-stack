# Deployment Order

This document gives one practical order for deploying the reference stack from scratch.

It is not the only valid order, but it is a good sequence if you want fewer moving parts at each step.

## Recommended Order

1. Prepare the host and storage.
   - install the base platform
   - prepare ZFS datasets or other persistent storage roots
   - confirm GPU device exposure and container strategy

2. Prepare the main LXC runtime.
   - create the main privileged Ubuntu LXC
   - mount model and application-data paths
   - confirm Docker works inside the container

3. Bring up the local LLM path first.
   - prepare `/etc/llama`
   - prepare `/mnt/ai-models/llm`
   - build and configure `llama.cpp`
   - verify the OpenAI-compatible endpoint

4. Bring up core supporting services.
   - `search`
   - `qdrant`
   - `voice`
   - `docling`

5. Bring up the media path.
   - `media`
   - verify ComfyUI
   - verify preferred image and video workflows

6. Bring up user-facing application layers.
   - `openwebui`
   - optional automation and chat systems

7. Add optional gateway and convenience layers.
   - `proxy`
   - `mcp-playwright`
   - maintenance helpers

## Why This Order Works

- It validates storage and runtime assumptions early.
- It gets the model-serving path working before the UI layer.
- It keeps debugging scope smaller when something fails.
- It avoids starting from the most integration-heavy components.

## Practical Validation Checklist

At each stage, verify the service before moving on:

- health endpoint or container logs
- network reachability from where it will actually be consumed
- persistent storage writes
- required model files or cache directories

If one layer is not healthy yet, avoid stacking more services on top of it.
