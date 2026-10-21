# Phase audit and unchanged-fixture measurements — 2026-10-21

The real `solid-gate-on-write` hook was rerun after adding internal planning diagnostics, before changing Codex tool-discovery or continuation behavior. No rule prompt, fixture expectation, model profile, or submission prompt was changed for this measurement.

## Comparable inputs

- Prospective source SHA-256: `04f8500811dc07352342c633b0c43b649f79ddf83fa5a8ed217d08aeba088523`.
- Existing isolated source-project fixture; absent `Sources/ReviewTarget.swift` reviewed as a buffer, with only the explicit DRY candidates.
- Locked profiles: Codex `gpt-5.6-terra`, Claude `claude-opus-4-5`, both timeout 1,000 seconds.
- Existing test: `tests/harness/flow_engine/test_solid_gate_on_write_live.py`.
- The earlier baseline predates the separately approved deterministic LSP fatal-call observation. This is a turn/token comparison, not a controlled accuracy experiment with unchanged rule semantics.

## Results

| Sample | Accepted workflow turns | Input including cache | Cached input | Output | Engine time | Outcome |
|---|---:|---:|---:|---:|---:|---|
| Codex, 2026-10-20 baseline | 22 | 1,007,342 | 947,456 | 12,924 | 108.46 s | Completed |
| Codex, fresh measurement | 5 | 269,558 | 232,704 | 7,557 | 200.50 s | Completed; DRY-3 accuracy assertion failed |
| Claude, 2026-10-20 baseline | 18 | 739,776 | 689,270 | 21,843 | 293.06 s | Completed |
| Claude, fresh measurement | 3, incomplete | 393,004 | 353,465 | 31,776 | No terminal workflow time | Interrupted after repeated malformed JSON |

Codex used five `flow_next` calls and one shell read call, with zero JavaScript/tool-not-callable errors. MCP rejected an inverted code-smells contract/implementation relationship once; the next submission corrected it. All 113 step completions, 40 metric observations, and ten rule results were preserved. LSP had no unavailable metrics. The class's DRY-3 result was **0**, but the unchanged fixture expects at least **1** for the inline cache-to-storage fallback. Consequently pytest correctly failed the live accuracy assertion; completion is not an accuracy pass.

Claude made eleven `flow_next` attempts and two `Read` calls. Eight submissions were rejected by Claude's tool-input JSON parser before reaching MCP. Three submissions were eventually accepted, but the two DRY target-pattern steps were still pending when the measurement child was stopped. The hook failed closed and the test preserved its artifacts. The stop occurred approximately 412 seconds after hook start; do not compare this incomplete elapsed time or token total as a successful review. The initial decision to stop followed seven consecutive malformed submissions; one further malformed attempt and a later accepted candidate batch are retained in the final transcript.

Codex usage is the final cumulative native transcript counter. Claude usage is summed once per unique assistant message (12 messages): 98 ordinary input + 39,441 cache-creation input + 353,465 cache-read input, and 31,776 output. These counters do not include undocumented/unreported usage. Cached inputs are included in the input total, not added again. No price estimate is inferred from raw token totals.

**Conclusion:** Codex's accepted turns fell from 22 to 5 and input tokens fell about 73%, but elapsed time increased versus the old baseline and the DRY expectation was missed. Claude's new sample is incomplete. These samples do not establish a general speed or accuracy improvement.

## Phase audit in the completed Codex run

The five `aggregate_phase_planned` events show the original assignments presented before each accepted submission:

| Submission | Combined work |
|---|---|
| 1 | Code-smells, frontmatter, ISP, LSP, OCP, and SRP classifiers, plus both DRY search-term assignments |
| 2 | Corrected code-smells classification, both DRY candidate selections, and remaining non-DRY exception classifications |
| 3 | All four selected DRY target/candidate pairs, with inspection and classification together |
| 4 | Both DRY target-pattern analyses |
| 5 | Both DRY exception classifications |

The recorder preserves original step/instance identities, typed deferrals, prerequisite IDs, and policy ownership. These internal audit records are absent from the native model transcript. Deferral counts are **not** additional model turns: each logical phase can record work assigned to another workflow boundary, and several logical phases share one combined presentation. For example, the first event has 801 cross-boundary records, not 801 blocked submissions.

## Validation after audit implementation

- All non-live groups: **3,048 passed, 270 subtests passed, 4 skipped**. The skips are abstract schema-fixture base cases whose concrete subclasses run.
- Shared live flow-engine contract suite: **10 passed in 451.87 seconds**, five Codex and five Claude cases, including delegation and conditional routing. Artifacts are under `.solid-coder/.artifacts/test/{codex,claude}/e2e/flow-engine/workflow-contract/`, timestamped from `20261021T171919Z` through `20261021T172556Z`.
- Real gate measurement suite: **2 failed in 618.34 seconds**, for the distinct Codex DRY accuracy miss and interrupted Claude malformed-JSON run described above. No expectation was weakened or failure excluded.

## Preserved evidence

### Codex

- Run: `706d9b4757314450a3459dba0392a592`.
- Child session: `01a15f6f-6c71-7513-ba17-154841f4a1c0`.
- Artifacts: `.solid-coder/.artifacts/test/codex/e2e/gate/solid-gate-on-write/20261021T170817Z-e78c4150/`.
- Canonical project audit: `/Users/crowea/.solid-coder/-private-var-folders-42-g1w_3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-upo6mymm/`.
- Native transcript: `/Users/crowea/.codex/sessions/2026/10/21/rollout-2026-10-21T13-08-20-01a15f6f-6c71-7513-ba17-154841f4a1c0.jsonl`.

### Claude

- Run: `c08cc0aa93df4f5297214c0449bf76ff`.
- Child session: `8425902d-8b99-47ed-9566-9b3d451a615c`.
- Artifacts: `.solid-coder/.artifacts/test/claude/e2e/gate/solid-gate-on-write/20261021T171141Z-3f4f53eb/`.
- Canonical project audit: `/Users/crowea/.solid-coder/-private-var-folders-42-g1w_3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-vy2l1k4d/`.
- Native transcript: `/Users/crowea/.claude/projects/-private-var-folders-42-g1w-3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-vy2l1k4d/8425902d-8b99-47ed-9566-9b3d451a615c.jsonl`.

## Codex availability investigation (after measurement)

The older failing session's JavaScript lookup failed before MCP invocation, so it could not produce a workflow validation rejection. In the successful retry, the same normalized tool name failed at 15:56:27, appeared in `Object.keys(tools)` at 15:59:06, and subsequently worked. That chronology proves changing availability, not that enumeration itself repaired it. The new measurement used the normalized name successfully without discovery.

The delegated configuration supplies the correct checkout server and interpreter, but the Codex adapter forwards only command and arguments. It does not make this essential MCP server required. [Official Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp#other-configuration-options) specifies a default 1,000 ms initial-catalog grace period for optional MCP servers; required servers use their startup timeout and fail startup if they cannot initialize. The installed CLI is 0.153.0 and its binary includes the optional-startup-grace configuration key.

Three read-only initialize/tools-list exchanges against the actual delegated server, in an isolated project with health-check session type, succeeded in 0.740, 0.795, and 0.760 seconds. Both `flow_start` and `flow_next` were present every time, with no stderr. This is close to the documented grace period, but does **not** prove the earlier failures exceeded it.

There are no matching child-session rows in the local Codex logs database. The production command executor discards successful child stdout/stderr after validation, so the earlier startup timeline cannot be reconstructed from that audit.

### Controlled startup reproduction

Two sequential read-only probes used the same installed CLI, `gpt-5.6-terra`, `--ignore-user-config`, health-check session environment, production flow-engine entry point, and a 30-second startup timeout. Both inserted a deliberate 15-second delay before starting that server. The only registration difference was `required = false` versus `required = true`. The model's first and only tool call was `text(typeof tools.mcp__solid_coder_flow_engine__flow_next);`; neither probe started a workflow, invoked `flow_next`, enumerated tools, or edited project files.

| Registration | First lookup | Total probe elapsed | Child session |
|---|---|---:|---|
| Optional | `undefined` | 6.04 s | `01a15f82-b080-7421-85f2-bd0639e22364` |
| Required | `function` | 22.02 s | `01a15f82-c6bb-73f2-b025-76601304b553` |

Native transcripts preserve the exact JavaScript and returned values:

- `/Users/crowea/.codex/sessions/2026/10/21/rollout-2026-10-21T13-29-22-01a15f82-b080-7421-85f2-bd0639e22364.jsonl`.
- `/Users/crowea/.codex/sessions/2026/10/21/rollout-2026-10-21T13-29-28-01a15f82-c6bb-73f2-b025-76601304b553.jsonl`.

This reproduces a real startup/catalog race: an optional server can be absent from the first model call; required registration waits for it. It is consistent with the historical failures, but does not retrospectively prove their startup duration. No production registration or continuation prompt was changed during this investigation.

The proposed narrow fix is to mark the essential delegated flow server required, forward its startup settings through the Codex configuration adapter, and preserve startup diagnostics. Tests must cover successful delayed initialization and failure before model execution when the required server cannot start. This is a follow-up, not a claim that the production availability issue is already fixed. Tool discovery instructions, aliases, and renaming are not substitutes for correct startup coordination.
