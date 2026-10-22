# Flat Submission Experiment — 21 October 2026

## Setup

One nested and one flat run per backend, executed sequentially through the real
write hook. Both variants inherit the existing gate test, fixture, and assertions.
No bundled workflows, rule prompts, observation schemas, or scoring were changed.
Models: Codex `gpt-5.6-terra`; Claude `claude-opus-4-5`; timeout 1,000 seconds.
Source SHA-256: `04f8500811dc07352342c633b0c43b649f79ddf83fa5a8ed217d08aeba088523`.

```sh
python3.12 -m pytest tests/harness/flow_engine/test_solid_gate_on_write_live.py tests/harness/flow_engine/test_flat_submission_gate_live.py -v -s
```

All four live tests passed. Non-live validation: 3,066 distinct tests passed,
four existing skips. SourceKit-dependent tests require local service access;
the sandboxed run failed those checks and the unrestricted run passed them.

## Results

Input includes cached tokens; cache columns are subsets, not extra tokens to add.
Claude input also includes cache-creation input. Claude usage is deduplicated by
assistant message ID; Codex uses the final cumulative transcript token event.

| Backend | Format | Full hook seconds | Engine seconds | Input | Cache read | Cache write | Output | Accepted turns | Submission attempts | Local syntax/JSON errors | MCP step rejections |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Codex | Nested | 183.29 | 179.12 | 256,850 | 222,464 | 0 | 6,721 | 5 | 5 | 0 | 0 |
| Codex | Flat | 181.71 | 176.38 | 253,898 | 223,232 | 0 | 6,611 | 6 | 6 | 0 | 0 |
| Claude | Nested | 286.25 | 269.98 | 295,809 | 254,165 | 41,570 | 21,885 | 5 | 7 | 2 | 1 |
| Claude | Flat | 242.31 | 223.49 | 198,170 | 166,432 | 31,672 | 17,921 | 5 | 6 | 1 | 0 |

First accepted submission, measured from engine start: Codex 100.36 → 72.73
seconds; Claude 95.28 → 89.50 seconds. The faster first Codex response did not
translate into a meaningful end-to-end improvement in this sample.

## Interpretation

- Codex: essentially unchanged total time (0.9% lower) and input (1.1% lower).
  All eight DRY candidate assignments were presented together (`a30`–`a37`),
  but the model voluntarily submitted four, then four. The extra accepted turn
  was not an MCP planning boundary or a schema rejection. The flat instructions
  explicitly allow subsets; a later experiment can request all pending work in
  one call while retaining partial recovery. This wording was not changed during
  these measurements.
- Claude: 15.4% lower full-hook time, 33.0% lower input, and 18.1% lower output.
  There was one fewer malformed-JSON retry. The format did not eliminate JSON
  failures: the flat run still had one.
- Claude's nested run also copied declaration descriptions into declaration-ID
  fields. Existing MCP coverage validation rejected the incorrect IDs and the
  model corrected them. This was distinct from its two pre-MCP JSON parse errors.
- All 38 metric value/severity pairs matched between Claude variants. Codex
  differed on the reviewed class's DRY-1 repository reuse count and DRY-2
  repository duplicate-location count: both were 0/COMPLIANT in nested and
  1/SEVERE in flat. All other metric value/severity pairs matched. These differences
  have not been independently adjudicated as an accuracy improvement.
- Passing the gate assertions does not establish complete classification
  accuracy. One sample per cell cannot establish a reliable performance effect.
  Keep `nested` as the default and `flat_array` opt-in.

## Preserved evidence

Machine-readable comparison, including absolute artifact, canonical audit,
transcript paths, usage details, and metric differences:

`.solid-coder/.artifacts/test/codex/e2e/gate/solid-gate-on-write/20261022T023026Z-d58e51b0/flat-submission-comparison.json`

| Backend / format | Run ID | Test artifact directory suffix |
|---|---|---|
| Codex nested | `11ef9910c4b34a1d969b23dd93e2d38a` | `codex/e2e/gate/solid-gate-on-write/20261022T023026Z-d58e51b0` |
| Codex flat | `2af5a0ed9c47446aa18276e938a8e3e7` | `codex/e2e/gate/solid-gate-on-write/20261022T023816Z-f920e683` |
| Claude nested | `ec52504ea64448e68036f462f72453e3` | `claude/e2e/gate/solid-gate-on-write/20261022T023330Z-0b7b0d98` |
| Claude flat | `e9ec0865b3f34eec993e011fe8d50666` | `claude/e2e/gate/solid-gate-on-write/20261022T024118Z-31047811` |

Suffixes are under `.solid-coder/.artifacts/test/`. Each directory contains
`canonical-audit-path.txt`, the captured audit, exact prospective source, copied
profile and project configuration, hook output, and full hook elapsed seconds.
The canonical audit remains in the user's `.solid-coder/<project-slug>/` folder.
