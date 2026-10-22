# Bundled rule migration validation — 2026-10-22 UTC

## Scope

The inventory found all eleven existing review-rule families already ported to
`workflows/review/rules/<id>/workflow.yaml`. This close-out checks those real
bundled workflows through the existing review entry points, fixes stale live
contracts, and clarifies the approved DRY forwarding-body classification.
The model profiles are the existing Codex `gpt-5.6-terra` and Claude
`claude-opus-4-5`, each with the existing 1,000-second timeout.

| Workflow | Scope | Current metric IDs |
|---|---|---|
| srp | Unit | SRP-1, SRP-2, SRP-3 |
| ocp | Unit | OCP-1, OCP-2, OCP-3; OCP-1 has two observations |
| lsp | Unit | LSP-1, LSP-2, LSP-3, LSP-4; unresolved outcomes remain explicit |
| isp | Unit | ISP-1, ISP-3, ISP-5 |
| dry | Unit | DRY-1, DRY-2; repository and within-unit observations remain separate |
| code-smells | File | CS-1, CS-2, CS-3 |
| structured-concurrency | Unit | SC-1 through SC-6 |
| swiftui | Unit | SUI-1 through SUI-10 |
| frontmatter | File | FM-1 through FM-5 |
| unit-testing | File | TEST-1 through TEST-6 |
| ui-testing | File | UITEST-1 through UITEST-5 |

Numeric observations are derived by MCP from the authored sources and reducers.
SwiftUI's injection-style observation remains a model classification scored by
MCP. The workflows use the existing applicability filters, source operations,
exception schemas, and scoring contracts.

## Changes made during close-out

- OCP live expectations now match its deterministic contract: dependency analysis,
  four metric observations with exact identities, values `2 / 0 / 0 / 0`, and
  audited exception classification. The old live expectation named removed steps.
- LSP live expectations now match its deterministic contract: `fatal_calls`
  independently detects the fixture's fatal call. The inferred `isPlaying` type
  leaves full contract coverage unresolved, so LSP-3's contract observation and
  LSP-4 are explicitly unavailable with reasoning/evidence instead of fabricated
  numeric zeros. The relationship scenario retains its separate five-observation
  contract and expects no unavailable metrics.
- A shared non-live check compares OCP/LSP live metric expectations against their
  deterministic scenarios, preventing the two sets from silently diverging.
- Codex protocol checks retain recovered errors in their evidence whether the
  model prints full MCP envelopes or only their text. Same-session terminal
  server evidence establishes completion. Failed starts, unanswered calls,
  unrelated sessions, and failed workflows still fail their existing tests.
  A new failing test reproduced the inconsistent recovery behavior before its
  correction.
- DRY's original current Codex sample returned zero for identical forwarding
  bodies. The prompt now explicitly classifies those bodies as IDENTICAL even
  when the callee contains shared logic. Its existing prompt-contract test failed
  before that clarification and passed afterward. Fixtures, thresholds,
  candidate search, observation schemas, and scoring are unchanged.
- SPEC-065's original compliant-wrapper expectation is marked superseded by the
  user's later approved duplicate-wrapper policy; the historical evidence remains.

## Final non-live checkpoint

All five groups were run after the final workflow edit:

| Group | Passed | Existing skips |
|---|---:|---:|
| Workflow engine | 1,060 | 0 |
| MCP/source | 1,301 | 4 |
| Remaining harness/hooks/integration/validators/coding/testing | 160 | 0 |
| Scripts | 253 | 0 |
| Apple build and skill scripts | 295 | 0 |
| Total | 3,069 | 4 |

SourceKit tests ran with access to the local service. Live tests and the separate
live health-check integration suite were excluded from these non-live groups.

## Live evidence and initial failures

The initial shared matrix ran both backends for every rule plus the existing
ISP extension, Code Smells boundary, and additional DRY scenarios: **27 passed,
5 failed in 1,836.99 seconds**. It began before the live-harness corrections were
loaded. Its failed records are preserved rather than reported as clean runs.

| Initial failure | Artifact directory under `.solid-coder/.artifacts/test/` | Finding |
|---|---|---|
| Codex SRP | `codex/e2e/review/srp/20261022T030626Z-3289fc6b` | Completed with `6 / 2 / 2`; recovered JavaScript error exposed the unwrapped-response assertion inconsistency |
| Codex LSP | `codex/e2e/review/lsp/20261022T031025Z-e01a40f1` | Completed; stale metric expectations and a recovered incorrect run-ID call |
| Claude LSP | `claude/e2e/review/lsp/20261022T031141Z-be43b884` | Completed; stale measured-versus-unavailable expectations |
| Codex identical DRY wrappers | `codex/e2e/review/dry-extracted-helper/20261022T031618Z-c8fe7a4a` | Completed with `0 / 0 / 0`, differing from locked `0 / 0 / 2`; also recovered a script error |
| Codex Frontmatter | `codex/e2e/review/frontmatter/20261022T033041Z-73b36c0e` | Completed with `1 / 0 / 0 / 0 / 0`; recovered-call assertion inconsistency |

An earlier OCP precheck also failed on stale step names, while the actual workflow
completed with `2 / 0 / 0 / 0`. Its artifact is
`codex/e2e/review/ocp/20261022T030430Z-f02217d2`. Both OCP matrix cases passed
after the shared expectation correction.

Revalidation of preserved SRP and LSP runs against the corrected assertions
passed without rerunning the models. The DRY wrapper discrepancy remained a
real classification mismatch; it was not hidden by the protocol correction.

## Fresh affected-case verification

Completed. After the final non-live checkpoint, fresh Codex SRP and Frontmatter,
both LSP basic/relationship cases, and all eight DRY cases produced their locked
results. The 14-case command reported **13 passed, 1 failed, 4 subtests passed in
757.44 seconds**. Its one failure was a Claude startup refusal before any
`flow_start`, not a submitted classification or scoring mismatch.

That failed attempt is preserved at
`claude/e2e/review/dry-rounding-variation/20261022T035123Z-604e003b/`.
Its initialization lists the current `plugin:solid-coder:flow-engine` as
connected and the stale `plugin:solid-coder:solid-coder-flow-engine` entry as
failed. Tool discovery returned the current flow tools, but the model reported
the stale connection failure and stopped without calling them. There is no flow
audit for that attempt. One retry with identical inputs, instructions, profile,
and configuration passed in **60.70 seconds**. This intermittent startup
misinterpretation remains a limitation; the initial failure is not a clean pass.

All 14 affected case configurations therefore have passing fresh live evidence,
including four unavailable-metric subtests. Together with the initial matrix's
unchanged passing cases, this covers all eleven rule families on both backends,
ISP extension-first review, Code Smells boundaries, four DRY scenarios, and
LSP relationship inspection. No fixture expectations were relaxed.

The successful fresh DRY wrapper results are `0 / 0 / 2` on both models. The
earlier Codex zero result remains in the initial-failure table above. This is
validation of the locked scenarios, not a repeated-sample accuracy estimate.

Each artifact below is under
`.solid-coder/.artifacts/test/<backend>/e2e/review/<scenario>/<artifact>/`.

| Backend / scenario | Artifact | Run ID |
|---|---|---|
| codex / srp | `20261022T033952Z-bbbd63f7` | `c79db75b300143ca9556800692724a98` |
| codex / frontmatter | `20261022T034117Z-78d42e25` | `5cbb742f5bc34e798cae8c79caf5c356` |
| codex / lsp | `20261022T034200Z-5da3e38c` | `5eaed3d291f746da99212a80d0c5be38` |
| codex / lsp-relationships | `20261022T034323Z-df66a4c5` | `2756445ba2384eacab683f2bd9909d8d` |
| codex / dry-exact-protocol-reuse | `20261022T034554Z-cce79746` | `1c5052457d5d4f6e9f2e89d94e718766` |
| codex / dry-extracted-helper | `20261022T034657Z-15a4eda4` | `513317082ad24725a61babd3f4bc7f42` |
| codex / dry-rounding-variation | `20261022T034733Z-2a548824` | `2c312fb3b13846c89f5af84847c8ba20` |
| codex / dry | `20261022T034805Z-e894bbef` | `69bc3230e6b045da91fecbf0c290ec78` |
| claude / lsp | `20261022T034233Z-01a7b9aa` | `d58a0854b0fe4c09986b5b07d2324c1c` |
| claude / lsp-relationships | `20261022T034437Z-aa618309` | `4f282e9ea9d24c1fb036375d197f5703` |
| claude / dry-exact-protocol-reuse | `20261022T034911Z-c8ff1f81` | `77cbf0e4623d4da9a3e28534854e5c74` |
| claude / dry-extracted-helper | `20261022T035024Z-987ba737` | `4f8c2bae9c0748538b1b7b23e6de5288` |
| claude / dry-rounding-variation | `20261022T035257Z-3486b5ce` | `2ce5756272354f8eaa11a2bdf264da3d` |
| claude / dry | `20261022T035136Z-b05e36ed` | `1103cda717c64ec2a6f1cd6e1874ab7f` |

```sh
python3.12 -m pytest tests/harness/flow_engine/test_srp_validation_live.py::TestCodexSRPValidationLive tests/harness/flow_engine/test_frontmatter_validation_live.py::TestCodexFrontmatterValidationLive tests/harness/flow_engine/test_lsp_validation_live.py tests/harness/flow_engine/test_lsp_repository_relationship_live.py tests/harness/flow_engine/test_dry_validation_live.py -v -s --tb=short
```

Every live run retains its workflow events, submissions, normalized rule results,
model profile, and transcript under the existing artifact layout. Canonical
runtime audits remain under the user-level `.solid-coder/<project-slug>/` tree;
the repository artifact directories are ignored test copies. No commit, release,
default submission-format change, or model-profile change is part of this work.
