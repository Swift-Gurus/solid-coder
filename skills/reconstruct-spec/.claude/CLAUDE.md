# reconstruct-spec — Blind Spec Reconstruction

## Purpose

Reads arch.json (and ONLY arch.json) and produces a reconstructed spec describing what the architecture would deliver. The reconstruction must be blind to the original spec — this prevents confirmation bias. A separate agent then diffs the reconstructed spec against the original to find gaps.

## Design Decisions

- **Blind reconstruction** — the agent never sees the original spec. This is the entire point. If it reads the spec, it'll just confirm the architecture covers it.
- **Read-only tools** — only Read and Write. No Grep, no Glob, no Bash. The agent reads one file and writes one file. No searching the codebase, no loading rules.
- **Honest reconstruction** — if the architecture doesn't have a component for something, the reconstructed spec must not mention it. Missing capabilities are the signal the diff agent needs.