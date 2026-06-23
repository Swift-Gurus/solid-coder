---
name: stale-gate-output-bug
description: Gate accumulates stale review-output.json files in project slug dir, causing cross-file violation bleed
metadata:
  type: project
---

Stale `review-output.json` files persist in `~/.solid-coder/<project-slug>/gate/<session_id>/` across health check invocations within the same session. The gate globs `*/review-output.json` to collect violations, so stale files from earlier checks on unrelated files bleed into subsequent checks.

**Why:** `hc_checker.py` uses `gate/<session_id>/` as a shared output dir (not per-invocation timestamped dir). The fix plan is in `GATE-OUTPUT-PATH-HANDOFF.md`.

**How to apply:** When the gate produces unexpected DRY/SRP violations that reference other project files (not the file being written), check if stale output files exist:
```
ls ~/.solid-coder/<project-slug>/gate/<session_id>/
```
Delete the directory to clear stale results before re-running the check.

The proper fix (not yet implemented): use `get_output_path("health")` per invocation to get a unique timestamped dir — see [[project_pipeline_direction]] and `GATE-OUTPUT-PATH-HANDOFF.md`.
