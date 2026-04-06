# Private to Public Transition Plan

This document defines a clean transition path from the current private draft to a first public release.

The goal is not only to make the repository safe.
The goal is also to make the public version focused, professional, and easy to understand.

## Current Situation

The repository is already in good technical shape as a private draft:

- sanitized examples
- deployment-oriented documentation
- public-safe MCP scripts
- practical stack examples

What remains is mostly publication shaping rather than core technical work.

## Public Release Strategy

Use a deliberate transition instead of simply flipping repository visibility from private to public.

Recommended approach:

1. keep the current private repo as the working draft
2. decide which files belong in the public branch or release
3. remove or rewrite internal-only files
4. perform one final audit
5. only then make the repository public

## Files That Should Stay Private or Be Rewritten

These files are useful during private staging, but should not be exposed as-is in the first public release:

- `SECURITY.md`
- `STATUS.md`
- `docs/publication-readiness-checklist.md`
- `docs/screenshot-review.md`
- any future internal-only release notes

## Why `SECURITY.md` Should Not Be Public As-Is

The current `SECURITY.md` is an internal publication-guardrail document.

It is useful for private staging because it explains:

- what must be audited
- which patterns to search for
- what kinds of files are dangerous

But for a public repository, that file is the wrong shape.

In a public repository, `SECURITY.md` should normally be one of these:

- a short vulnerability reporting policy
- a statement that the project is documentation-first and provided without warranty
- a simple disclosure contact/process document

It should not primarily read like a private pre-publication checklist.

## Recommended Public-Facing Replacements

Before making the repository public, replace internal staging documents with smaller public-facing versions where needed.

Examples:

- replace the current `SECURITY.md` with a short public security policy
- keep `LICENSE.md`
- keep `CONTRIBUTING.md`
- keep `docs/release-scope.md` only if it still reads well for public readers

## Files Likely Fine for the First Public Release

- `README.md`
- `LICENSE.md`
- `CONTRIBUTING.md`
- the architecture, hardware, storage, and deployment docs
- `docs/deployment-order.md`
- examples under `examples/`
- scripts under `scripts/`

## Practical Pre-Public Checklist

1. Remove or rewrite internal-only files.
2. Run one final secret and private-address scan.
3. Re-read the repository as if you were an outside user.
4. Confirm that the first-screen README matches the actual scope.
5. Confirm that every example still uses placeholders and example hostnames.
6. Confirm that screenshots are still acceptable.
7. Only then switch visibility to public.

## Scope Principle

The public repository should feel intentional.

A good first public release is not the same thing as a perfect mirror of the private draft.

It is better to publish:

- a smaller, cleaner public repository

than:

- a technically complete but inward-facing staging repository
