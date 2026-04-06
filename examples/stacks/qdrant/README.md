# Qdrant Stack Example

This directory contains a public-safe environment example for a Qdrant deployment with optional backup support.

## What It Shows

- HTTP and gRPC port shaping
- storage and backup paths
- optional API key usage
- a simple remote-backup configuration pattern

## How to Use It

- copy `.env.example` to `.env`
- replace placeholder keys and remote URLs
- adjust storage paths to your own layout
- keep backup configuration only if you actually use it

## Notes

- the reference stack uses Qdrant as supporting infrastructure, not as the center of the system
- the example is meant to show environment categories, not to prescribe one exact deployment pattern
