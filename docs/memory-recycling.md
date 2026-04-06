# Memory Recycling

This document describes a practical pattern for reclaiming memory in a local AI stack without fully restarting every service.

The reference stack uses two complementary approaches:

- `llama.cpp` child processes are allowed to exit after inactivity
- `ComfyUI` is asked to unload models and free memory after idle periods

This is not a universal recipe, but it is a useful pattern for single-operator systems that run large models on shared hardware.

## Why This Matters

Large local AI workloads tend to hold on to memory aggressively:

- LLMs keep RAM and VRAM tied up while a child server stays alive
- diffusion workflows keep model weights, caches, and allocations warm for future prompts

That can be good for latency, but bad for mixed workloads on one machine.

The goal of memory recycling is to keep the stack responsive without forcing full restarts every time a model is no longer needed.

## Part 1: `llama.cpp` Idle Exit

The reference stack uses `llama.cpp` router mode with per-model presets in `models.ini`.

A key setting is:

```ini
sleep-idle-seconds = 1200
```

This tells a spawned child server to exit after being idle for the configured number of seconds.

Representative pattern:

```ini
[example-chat-model]
model = /mnt/ai-models/llm/example-chat-model-Q5_K_M.gguf
ctx-size = 32768
n-gpu-layers = 999
warmup = 0
parallel = 2
sleep-idle-seconds = 1200
```

### Practical Interpretation

- shorter values free memory more aggressively
- longer values keep models hot for repeated use
- very small models can tolerate much shorter idle timers
- large chat or vision models often benefit from a middle ground such as `600` to `3600`

### Useful Heuristic

- `60` to `300` seconds for light or specialized models
- `600` to `1200` seconds for commonly used chat or coding models
- `3600` seconds for a default preset when you want lower churn

### Trade-Off

If you set idle exit too aggressively, you save memory but pay more reload latency later.

If you set it too loosely, you keep better responsiveness but waste memory on models you are no longer using.

See also:

- [llama-backend.md](llama-backend.md)
- [../examples/llama/models.ini.example](../examples/llama/models.ini.example)

## Part 2: ComfyUI Idle Unload

The reference stack uses a small sidecar process that polls ComfyUI and calls its `/free` endpoint after a period of inactivity.

The basic idea is:

1. check `/queue`
2. if nothing is running or pending for long enough, call `/free`
3. optionally ask ComfyUI both to unload models and to free memory

Representative environment values:

```env
IDLE_SECONDS=900
POLL_SECONDS=15
FREE_COOLDOWN_SECONDS=300
FREE_UNLOAD_MODELS=true
FREE_MEMORY=true
STARTUP_WAIT_SECONDS=900
LOG_MODE=quiet
```

And the key request shape is:

```json
{
  "unload_models": true,
  "free_memory": true
}
```

### Practical Interpretation

- `IDLE_SECONDS` controls how long ComfyUI must stay inactive before cleanup starts
- `POLL_SECONDS` controls how often the queue is checked
- `FREE_COOLDOWN_SECONDS` prevents spammy repeated unloads
- `FREE_UNLOAD_MODELS=true` tells ComfyUI to unload model weights
- `FREE_MEMORY=true` asks it to release memory more aggressively

### Why a Sidecar Helps

ComfyUI itself is focused on generation, not on host-level memory etiquette.

A tiny sidecar is useful because it:

- keeps the cleanup policy outside the main container
- can be tuned without modifying the application itself
- works well for shared machines where image generation is bursty rather than constant

See also:

- [../examples/stacks/media/README.md](../examples/stacks/media/README.md)

## Manual vs Automatic Recycling

There are two useful operating modes.

### Automatic

Use idle timers and sidecars when:

- the machine is shared across many workloads
- you want memory to recover without operator action
- workloads are bursty and idle periods are common

### Manual

Use explicit unloads when:

- you know you are done with a large job
- you want to hand the machine over to another workload immediately
- you are debugging memory pressure

For ComfyUI, the manual version is simply calling `/free` with the desired payload.

## Design Principle

The best practical pattern is usually:

- keep hot models alive for a reasonable time window
- do not keep everything hot forever
- recycle memory at the child-process or app level before reaching for full service restarts

That gives a better balance between responsiveness and resource recovery than either extreme.

## What This Does Not Solve

Memory recycling does not fix:

- bad model choices for your available VRAM or RAM
- fragmentation or allocator issues in every runtime
- version-specific GPU stack bugs
- workload bursts that genuinely require more memory than the machine has

It is a practical pressure-management technique, not a substitute for sound capacity planning.
