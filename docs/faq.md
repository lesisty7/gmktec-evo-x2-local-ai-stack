# FAQ

## Why use LXC instead of a VM for the main AI runtime?

Because this design prioritizes low overhead, easy storage sharing, and direct access to AMD GPU devices from a Linux userspace environment.

## Will this setup give a Windows VM direct GPU acceleration?

No. This reference architecture is explicitly LXC-first and does not document GPU passthrough to a Windows VM.

## Why run llama.cpp directly in the LXC instead of in Docker?

Because it keeps the serving path simpler and closer to the hardware while still allowing the rest of the stack to stay containerized.

## Why are there so many mounts?

The current source layout uses many bind mounts for clear separation of concerns. That is arguably overkill for a smaller setup, but it makes persistence and service ownership easier to reason about.

## Why split `llm` and `sd` models?

Because language and diffusion workloads have different storage patterns, lifecycle needs, and supporting assets.

## Why keep both a preferred image path and a fallback image path?

Because a newer workflow path may be better or broader, while an older simpler path can still be useful as a stable fallback.

## Is every tuning choice here universally recommended?

No. This repository documents a practical working setup, not a universal recipe. Some settings are straightforward best practices, while others are context-dependent trade-offs.

## Is `sync=disabled` recommended?

Not universally. It is a throughput-oriented trade-off that reduces durability guarantees in the event of power loss or crashes.

## Are the screenshots ready for publication?

Not automatically. They are useful, but they still require manual review before public release.
