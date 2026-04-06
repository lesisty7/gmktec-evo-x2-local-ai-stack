# Draft Roadmap

## Goal

Turn this private draft into a public-safe repository that is useful to other people building a similar local AI stack.

## Current Phase

Current phase: `final review before first public release`

What is already done:

- baseline repo structure
- English documentation pass
- public-safe example configs
- architecture docs
- model layout docs
- Proxmox helper docs
- from-scratch setup framing
- deployment-oriented example coverage across the main stack areas

## Next Steps

### 1. Security Review

- audit docs and examples for private details
- review screenshots before publication
- scan for secrets and private addresses
- review the final git history before first push

### 2. Documentation Polish

- tighten wording in the main docs
- add one or two simple diagrams beyond the Mermaid layout
- keep improving data persistence and storage guidance without overfitting to one machine

### 3. Example Quality

- add more public-safe example files only when they are genuinely useful
- avoid copying private stack files verbatim
- prefer templates over direct exports

### 4. Publication Readiness

- confirm the current license and disclaimer wording
- add credits or references where needed
- prepare the first public commit set
- verify that the first release scope stays intentionally small

## Explicit Non-Goals for Now

- publishing immediately
- mirroring all private configs
- sharing private reverse proxy rules
- sharing host-specific operational secrets
