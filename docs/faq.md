# FAQ

## Why use a privileged Ubuntu LXC instead of a VM for the main AI runtime?

Because this reference design is optimized for low overhead, simple storage sharing, and direct access to the AMD GPU device nodes that already exist on the Proxmox host.

In practice, this gives three benefits:

- `llama.cpp` can run very close to the hardware without adding a full guest VM layer
- Docker services inside the LXC can share mounted model trees and persistent data directories easily
- the whole stack stays operationally centralized in one Linux runtime instead of being split across multiple heavy guests

This is not a claim that VMs are always worse. It only means that for this specific stack shape, `Proxmox -> privileged Ubuntu LXC -> Docker` was the more practical choice.

## Do I need all of this?

Probably not.

Most people do not need the full stack documented in this repository.

What is documented here is a relatively rich reference setup that combines:

- a hypervisor layer
- one main AI LXC
- Dockerized support services
- local LLM serving
- image and video generation
- search, vector storage, UI, and automation components

That can be useful as a reference, but it is not the only sensible way to build a local AI machine.

For many people, a much simpler setup is the better starting point:

- just `llama.cpp`
- just `ComfyUI`
- one or two services without Proxmox
- one local Linux box without LXC or Docker nesting

This repository is designed so you can take only the fragments you need. You do not have to reproduce the full architecture to get value from it.

## Why not build this around Windows plus GPU passthrough?

Because that would be a different architecture with different trade-offs.

This repository documents a dedicated Linux-first AI host:

- Proxmox on bare metal
- host-managed ZFS storage
- host-managed AMD kernel stack
- one main privileged Ubuntu LXC for AI workloads

If your real goal is a GPU-accelerated Windows VM, this repository is not the right primary guide. Some ideas here still transfer, especially around storage layout and service separation, but the runtime model is different.

## How can my AI agent (`Codex`, `Gemini`, `Claude`, `Kimi`, and similar tools) help me with this kind of setup?

Very effectively, if the agent can work over SSH on the target machine.

In practice, an agent is most useful when it can:

- inspect the live filesystem
- read real configs
- check running services
- edit files in place
- restart only the service that matters
- validate the result with commands on the target machine

The easiest pattern is:

1. enable an SSH server on the target Linux machine
2. use a local Linux machine, or Windows with WSL, as the place where your agent runs
3. generate an SSH key
4. copy the public key to the target machine
5. let the agent work through SSH instead of copy-pasting long instructions by hand

Minimal example commands:

```bash
# on your local Linux machine or in WSL
ssh-keygen -t ed25519 -C "your-email-or-label"
ssh-copy-id user@your-target-host

# test access
ssh user@your-target-host
```

If `ssh-copy-id` is not available, you can still do it manually:

```bash
cat ~/.ssh/id_ed25519.pub
```

Then append that public key to:

```text
~/.ssh/authorized_keys
```

on the target machine.

Once SSH works cleanly, an agent usually becomes much more useful because it can inspect reality directly instead of relying on partial pasted snippets.

## Why run `llama.cpp` directly inside the LXC instead of in Docker?

Because it keeps the serving path simpler and removes one unnecessary layer around the LLM backend.

The design choice here is:

- run `llama.cpp` directly in the LXC
- run web tools and support services in Docker inside that same LXC

That keeps the model router close to ROCm and the GPU runtime while still letting the rest of the stack benefit from containerized service management.

## Why use router mode in `llama.cpp`?

Router mode is what makes this setup practical as a multi-model local backend.

Instead of rebuilding or manually reconfiguring a single-model server every time, router mode allows you to keep multiple presets in `models.ini`, expose them through one service boundary, and choose between chat, coding, embeddings, and multimodal presets in a cleaner way.

The important point is that router mode here is still controlled, not "load everything at once".

## Does router mode load many models at the same time?

Not in the reference setup.

The public examples document a configuration where:

- `LLAMA_MODELS_MAX=1`

in `router.env`.

That means the router is intentionally limited to one loaded model at a time. This reduces memory pressure and fits the reference approach to idle model recycling.

If you increase that value, you are making a different memory trade-off. That may be useful on some systems, but it is not the operating assumption documented here.

## Why are `router.env` and `models.ini` treated as operator-owned files?

Because they encode local deployment choices that are almost always machine-specific:

- model filenames
- active presets
- context sizes
- concurrency limits
- memory behavior
- host and port assumptions

Those are exactly the files that usually drift between machines. Keeping them clearly operator-owned makes the stack easier to understand and safer to update.

## Why are there so many mounts?

Because the reference stack strongly separates:

- model storage
- cache storage
- persistent application data
- checked-out service definitions

That gives better operational clarity. For example, it becomes easier to answer:

- what should be backed up
- what can be rebuilt
- what belongs to one service only
- what is shared by many services

At the same time, this is intentionally acknowledged in the docs as a bit overkill for a smaller homelab. Fewer mounts can be completely reasonable if you prefer a simpler setup.

## Why split `llm`, `sd`, and `cache` into separate top-level trees?

Because they behave differently over time.

`llm` model storage, diffusion model storage, and cache storage all have different:

- growth patterns
- cleanup needs
- backup value
- performance characteristics

Separating them makes it easier to tune storage and easier to understand what is actually consuming space.

## Why keep so much persistent data outside the container root filesystem?

Because container root filesystems are a poor place for long-lived AI assets and service state.

In this stack, the important persistent things live in mounted storage, not in the LXC rootfs:

- models
- caches
- database data
- vector database data
- ComfyUI data
- service-specific app state

That makes rebuilds and migrations much less painful.

## Why does the documentation care so much about ZFS tuning?

Because the host storage policy has a direct impact on how pleasant this machine is to operate.

The biggest practical ideas are not exotic:

- `atime=off`
- sensible compression choices
- no unnecessary dedup
- separate datasets for different types of data
- `autotrim` on SSD-backed storage

Those choices matter more in practice than many smaller "AI tuning" tweaks, especially once the machine starts accumulating large models and persistent service data.

## Do I need ZFS?

Probably not.

For many consumer and single-machine builds, `ext4` should be the default choice.

ZFS starts to make more sense when you are deliberately building around:

- two drives
- mirrored storage
- snapshot-oriented workflows
- stronger separation between datasets

Even in that case, it is still worth configuring it sanely, for example by disabling access time updates and thinking carefully about dataset policy.

On a single SSD, ZFS often adds complexity and extra write pressure without giving the main benefit people usually want from it. In many consumer scenarios, that makes `ext4` the safer default and ZFS the opt-in advanced choice.

## Is `sync=disabled` recommended?

Not as a universal rule.

It is a throughput-oriented trade-off and reduces durability guarantees during crashes or power loss. The repository mentions it as a contextual option, not as a blanket recommendation.

If you use it, you should understand exactly what you are trading away.

## Why does the stack keep both a preferred image path and a fallback image path?

Because image-generation stacks evolve faster than the rest of the system.

The current image path based on newer Flux workflows may be broader and more capable, but a simpler older path can still be valuable as:

- a known-good fallback
- a regression check
- a lower-friction recovery path when a newer workflow breaks

Keeping a fallback is a practical stability choice, not duplication for its own sake.

## Why does the repository publish examples instead of exact private configs?

Because a raw dump of a real environment is usually not safe to publish and often not that useful to other people anyway.

This repository tries to preserve:

- the architecture
- the working patterns
- the directory layout
- the important operational decisions

while removing:

- private IP ranges
- live tokens
- real secrets
- private routing maps
- machine-specific values that would confuse more than they help

## Are the example files meant to be copied unchanged?

Usually no.

They are meant to be structurally correct examples, not universal drop-in files. In almost every real deployment you will need to change:

- hostnames
- IP addresses
- ports
- storage paths
- model names
- image tags
- resource limits

The repository is intentionally concrete, but it is still a reference stack, not an installer.

## Are the screenshots automatically safe to publish?

No. Even when screenshots look harmless, they still need human review.

In this repository, screenshots are treated as documentation assets, not as inherently safe exports. Before public release, they should always be checked for:

- private hostnames
- revealing topology details
- operator identities
- URLs or addresses that should stay private

## Is every tuning choice here universally recommended?

No.

This repository documents a practical, working setup. Some parts are straightforward good practice. Others are informed trade-offs that made sense for this hardware and this operating style.

The safe way to read the repo is:

- copy the structure
- understand the rationale
- adjust the details to your own machine and goals

That is much closer to the intent of the project than treating every setting as a universal best practice.
