# Contributing

This repository is currently a private draft being prepared for future public release.

## Current Contribution Rules

- keep everything in English
- prefer public-safe examples over direct exports from private infrastructure
- do not add secrets, tokens, private URLs, or raw `.env` files
- do not copy private configs verbatim unless they are fully sanitized
- prefer short, focused documents over large raw dumps

## What Good Contributions Look Like

- architecture notes that generalize well
- example configs with placeholders
- setup guides that avoid private assumptions
- diagrams and screenshots after manual review
- concise operational notes that explain trade-offs

## What Not to Add

- production secrets
- host-specific internal network details
- browser session files
- local caches, logs, and generated artifacts
- internal backup files

## Editing Style

- use plain, professional English
- prefer stable terminology across documents
- explain trade-offs, not just commands
- avoid turning the repo into a private notebook

## Before Any Future Public Push

- complete the security review
- complete the screenshot review
- review example files line by line
- review git history, not only current files

## Recommended Local Safety Tooling

If you are working on this repository locally, install `pre-commit` and enable the included hooks:

```bash
pip install pre-commit
pre-commit install
```

The repository includes a `.pre-commit-config.yaml` with a secret-scanning hook so accidental credential commits are more likely to be caught before push.
