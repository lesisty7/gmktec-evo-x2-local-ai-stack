# Contributing

Thanks for considering a contribution.

This repository is a documentation-first project built around a practical local AI stack. Good contributions improve clarity, safety, and reusability for other builders.

## What Is Most Useful

The most valuable contributions are usually:

- clearer architecture and deployment notes
- better public-safe examples
- corrections to inaccurate or outdated documentation
- small scripts that improve reproducibility
- diagrams that explain real design choices

## Ground Rules

- keep everything in English
- prefer public-safe examples over direct exports from private environments
- do not commit secrets, tokens, private URLs, cookies, or raw `.env` files
- do not copy private configs verbatim unless they are fully sanitized
- prefer focused, readable documents over large dumps

## Contribution Style

Try to keep changes aligned with the style of the repository:

- use plain, professional English
- prefer stable terminology across files
- explain trade-offs, not just commands
- optimize for practical reuse
- avoid turning the repository into a personal notebook

## Examples and Configs

When contributing example files:

- replace live values with placeholders such as `replace_with_*`
- use example hostnames or neutral local names
- keep ports, paths, and service names easy to adapt
- include a short README when a stack needs context

If a real file is too environment-specific, prefer writing a smaller example instead of publishing a near-export.

## What Not to Add

- production secrets
- private IPs or internal hostnames that should not be public
- browser session state
- local caches, logs, and generated artifacts
- backup files and temporary recovery files
- firmware or binaries of unclear origin or licensing status

## Local Checks

If you are working on the repository locally, install `pre-commit` and enable the included hooks:

```bash
pip install pre-commit
pre-commit install
```

The repository includes a `.pre-commit-config.yaml` with a secret-scanning hook to help catch accidental leaks before commit.

## Pull Requests

Good pull requests are usually:

- small enough to review comfortably
- explicit about what changed and why
- careful about safety and anonymization
- consistent with the repository scope

If your change adds a new stack example or script, include enough documentation so another person can understand where it fits and how it should be adapted.
