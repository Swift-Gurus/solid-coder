# LSP-1 Provenance and Classification — Execution Plan

The agreed rule is recorded in `Spec.md`, under **Approved downstream LSP-1
contract**. This plan separates completed prerequisites from the runnable
workflow migration. LSP-2/3/4, legacy health-check behavior, user TOML settings
and locked fixture expectations remain unchanged.

## 1. Typed ownership boundary

- [x] Write failing tests before implementing ownership resolution.
- [x] Represent declaration evidence, SDK evidence and unresolved/ambiguous
  outcomes as typed variants.
- [x] Canonicalize repository paths and distinguish owned, external, excluded
  and unknown outcomes.
- [x] Reuse the existing exclusion-checking contract and one generic ownership
  resolver contract rather than duplicating interfaces.
- [x] Preserve typed evidence through JSON persistence without reevaluating
  later exclusion changes.

Validation: `tests/mcp-server/source/analysis/test_source_symbol_ownership.py`.
Its 11 tests pass. This is ownership classification of supplied semantic
evidence, not production semantic lookup or workflow replay integration.

## 2. Shared exclusion configuration

- [x] Test actual project TOML loading and configured glob semantics before
  wiring search, review eligibility and ownership to the same policy.
- [x] Preserve existing gate behavior and its project-root resolution.
- [x] Record the matched configured pattern in audit evidence through the
  shared exclusion capability.
- [x] Keep exclusion separate from verified external-contract provenance.

Hook exclusions still govern automatic writes. Explicit manual-review behavior
is not silently broadened by this change; search and ownership reuse the
project's configured patterns and preserve excluded scope separately.

## 3. Language-selected semantic adapter

- [x] Add failing adapter tests for declaration lookup versus value-type lookup,
  aliases, ambiguous names, inferred values and unavailable tooling.
- [x] Reuse the existing transport framing and typed decoding boundaries.
- [x] Resolve the value contract separately from the inspected destination.
- [x] Follow a semantically resolved binding to its explicit type annotation
  where supported; resolve that annotation semantically, not by name matching.
- [x] Retain unresolved outcomes when the installed service cannot establish
  the type. Never substitute the variable declaration for its type declaration.
- [x] Share one bounded document session across a snapshot's queries; keep
  reviewed code unwritten and clean up the owned subprocess.

Existing installed-toolchain probe:
`tests/mcp-server/source/analysis/test_sourcekit_symbol_contract.py`.
It demonstrates that existential value-type lookup can return null. That
limitation must remain visible in the production adapter.

## 4. MCP operation and replay

- [x] Register the typed source operation through the existing registry.
- [x] Derive inputs from the prepared source snapshot and project context,
  not LLM-supplied ownership or repository-root guesses.
- [x] Persist ordered inspection identities, query roles, provenance and
  limitations as engine-owned outputs.
- [x] Test aggregate execution boundaries and replay without repeated lookup.

## 5. Bundled LSP-1 migration

- [x] Replace only the LSP-1 inventory/ownership prompt with MCP-prepared facts.
- [x] Classify purposes using the four agreed categories, reasoning and evidence.
- [x] Reuse existing batch/identity coverage mechanics. Test pending omissions,
  invalid payloads, stale and invented identities, followed by correction.
- [x] Keep source facts authoritative and avoid relaying the full source again.
- [x] Count confirmed abstraction bypasses using authored YAML scoring.
- [x] Preserve unavailable coverage without reporting a compliant zero; retain
  confirmed violations alongside incomplete evidence.
- [x] Test empty complete inventories without a model turn.

## 6. Validation and activation

- [x] Run all non-live tests after production wiring and workflow migration.
- [x] Run locked Codex and Claude tests against the real bundled LSP workflow,
  with owned bypass, required external narrowing, diagnostic-only inspection
  and unresolved evidence fixtures.
- [x] Inspect persisted classifications, counts, unavailable outcomes and the
  aggregate/operation sequence before enabling the migrated rule.

The original catalog/LSP checks retain their locked expectations. Additional
Codex and Claude cases use the real distributed aggregate file-review bundle,
restricted to LSP by the existing project policy writer, and fixture-4.swift.
They check three purpose classifications plus one unresolved inspection,
retained severe findings, unavailable coverage and original event identities.

## Integration fixes discovered by acceptance tests

- A child step's own batched iteration inherited its parent's combined group,
  mixing different units' prompts. Its batch now carries the materialized owner
  identity. Inherited parent batches still combine normally.
- A completed conditional prefix still stopped later aggregate phase planning.
  Settled steps are now skipped before testing new phase boundaries; unresolved
  conditions and MCP-owned work still form boundaries.
- The shared operation-test driver did not inject its isolated project context,
  so rules-all could read the checkout's policy. It now uses the same explicit
  project context for policy loading and operation composition.

The real aggregate bundle is tested with two inspected units, not just one rule
instance. No LSP-specific behavior was added to the engine planner.

## Supported semantic scope

Swift explicit parameter/property annotations and simple identifier operands
resolve through SourceKit symbol evidence. Method/function call operands now
also resolve when the installed compiler supplies one supported substituted
return-type reference and independently confirms its identity. Callee ownership
does not substitute for return-contract ownership. Inferred identifier types,
unsupported aliases, composite or opaque returns, implicit pattern subjects,
other unsupported expressions, missing tooling and missing semantic context
remain explicit unavailable outcomes. References to prospective sibling snapshots
not opened by this session also remain unverified; stale on-disk declarations
cannot certify pending buffers.

Only compact verified expressions, line numbers and role ownership reach the
classifier. Full provenance remains in the operation event. Missing model
assignments stay pending; they are different from semantically unavailable
inspections. Confirmed bypasses alongside unavailable coverage use the existing
metric observation identity `confirmed_partial`, not a new scoring mechanism.

## Historical ownership-only checkpoint

New modules under `mcp-server/source/analysis/provenance/`:

- `source_declaration_symbol.py`
- `source_sdk_symbol.py`
- `source_unresolved_symbol.py`
- `source_symbol_ownership.py`
- `source_symbol_provenance.py`
- `source_declaration_ownership_resolver.py`
- `source_locationless_ownership_resolver.py`
- `source_symbol_ownership_resolver.py`

New test: `tests/mcp-server/source/analysis/test_source_symbol_ownership.py`.
Updated requirements: this directory's `Spec.md`.
This document records execution progress separately from the requirements.

The gate required separating declaration-path classification from locationless
SDK/unresolved classification. Both implementations use the same generic
resolver protocol, colocated with its first implementation. The coordinator
delegates to those injected implementations; no trivial factories or duplicate
resolver interfaces were added.

## Full non-live validation — 2026-10-18

- MCP tests: 1,216 passed, 95 subtests passed, 4 existing skips.
- Non-live flow-engine tests: 929 passed, 34 subtests passed.
- Harness, Stop hooks and hook dispatch: 174 passed, 2 subtests passed.
- Script tests: 253 passed, 66 subtests passed.
- Apple-build and skill-script tests: 288 passed.
- Total: 2,860 passed, 197 subtests passed, 4 existing skips.

The installed SourceKit probes ran successfully as part of the MCP suite.
Model-based integration suites and files named `*live*.py` were excluded from
the non-live run. The MCP suite was rerun after the generic engine fixes and
passed again. No local model is included and no original metric expectation
was changed.

## Final live validation — 2026-10-18

**6 passed in 312.50 seconds**: catalog compatibility, original LSP validation
and the new aggregate LSP case, each on locked Codex Terra and Claude Opus.

Both new aggregate runs completed without rejected submissions or failed steps.
For `InspectionConsumer`, the persisted operation recorded three verified
inspections and one unresolved inferred binding. Both models classified the
verified inspection IDs as abstraction bypass, required external narrowing and
non-behavioral inspection, in source order. MCP produced one SEVERE confirmed
bypass and an unavailable LSP-1 full-coverage outcome. LSP-2/3/4 remained zero
for this fixture. The operation completed before classification and no source
buffer was repeated in continuation responses.

Preserved evidence:

- Codex: `.solid-coder/.artifacts/test/codex/e2e/review/lsp-type-inspections/20261018T143020Z-a35713eb/flow-run/`
- Claude: `.solid-coder/.artifacts/test/claude/e2e/review/lsp-type-inspections/20261018T143124Z-503304b2/flow-run/`

The bundled LSP-1 migration is complete within the explicit semantic scope above.
The legacy health-check mode, user TOML and original LSP expectations were not
changed. This work is not a claim of complete semantic support for all Swift
expressions or languages, nor independent proof of model purpose judgments.

## Classification-only cleanup — 2026-10-19

The user accepted distinct prompts where needed. Do not expand the aggregation
engine merely to combine every LSP task into one prompt.

- [x] Add failing assertions against the real bundled workflows for repeated
  relationship classification, model arithmetic and empty counting markers.
- [x] Publish type-inspection classification and evidence as direct named
  outputs, consumed by existing collection conditions and metric scoring.
- [x] Keep candidate selection/coverage and per-candidate reading. Remove the
  child classification and make the parent the sole contract-violation classifier.
- [x] Remove unused relationship-assessment schema and model counting prose.
- [x] Update submission-shape and step-sequence assertions without changing any
  source fixture, metric threshold or locked expected score.
- [x] Run all non-live suites.
- [ ] Run locked Codex/Claude catalog and real bundled LSP live checks.

Focused checks passed: 13 workflow/classification tests and 2 subtests; the
repository-relationship test; and 7 original LSP contract tests. SourceKit
closed during sandboxed symbol queries; the approved outside-sandbox rerun
passed all 10 inspection-flow tests and 2 subtests. No source resolver or
aggregation engine change was made for this cleanup.

Non-live validation: **2,863 passed, 197 subtests passed, 4 existing skips**:
MCP 1,216; flow engine 932; harness/Stop/dispatch 174; scripts 253;
Apple-build/skill scripts 288. The new relationship live cases reuse fixture 3
and the existing model-neutral rule contract, expecting LSP values 0/1/0/0,
one selected declaration reading, and one subsequent violation classification.

The first Claude catalog attempt did not start a workflow. Its init event
reported both connected `plugin:solid-coder:flow-engine` and failed
`plugin:solid-coder:solid-coder-flow-engine` registrations; its final response
selected the failed name and reported CONNECTION_CLOSED. The checkout declares
the short names in `.claude-plugin/plugin.json` with plugin-root absolute paths
and the prefixed names in `.mcp.json` with relative paths. No plugin configuration
was changed as part of this LSP cleanup. Preserve this registration evidence
separately from rule accuracy or engine scoring results:
`.solid-coder/.artifacts/test/claude/e2e/flow-engine/workflow-catalog/20261019T115351Z-47f9ec75/claude-result.json`.

### Nested-condition acceptance failure — 2026-10-19 (resolved)

Closed in `64770ef`: nested step-output binding and file-rule applicability are
fixed. The final validation below supersedes this intermediate failing
checkpoint: 2,900 non-live tests, 228 subtests and all ten targeted live cases
passed, with four existing abstract-fixture skips. The original failure evidence
is retained below; it is not an outstanding task.

The new live inheritance checks reached the locked 0/1/0/0 scores on both
models but failed the required declaration-reading assertion. Audit events
showed the include condition reading `has_inheritance` in the child scope,
where that parent output was absent. Correct scores alone did not prove the
workflow executed its required steps. A recovered Codex JavaScript syntax error
was not the cause of this assertion failure.

Evidence: `review/lsp-relationships/20261019T115806Z-001f66b7/flow-run/`
under Codex test artifacts and
`review/lsp-relationships/20261019T115846Z-c270ab60/flow-run/`
under Claude test artifacts. The Claude catalog retry passed.

- [x] Reproduce the scope problem with a model-free, three-level nested workflow.
  Include conditions read the parent's outputs/parameters and the current item;
  child step conditions read mapped child inputs. Verify durable skips and replay.
- [x] Preserve the typed declaring context when materializing an include, and
  use the child context only for the child's own step conditions.
- [x] Compile generated rule filters against their explicit adapted source
  binding instead of relying on accidental child-parameter visibility.
- [x] Separate enrolled-source selection from single-member materialization as
  required by the gate, reusing the existing condition conjunction and scope adapters.
- [x] Resolve the file-rule filter limitation through shared nested step-output
  binding, including `steps.prepare_review.outputs.review_file.applicability.tags`.
- [x] Rerun all non-live suites and the locked live cases after that fix; the final
  matrix contains ten cases, including both real write-gate profiles.

At the intermediate checkpoint, the focused rerun had 17 passing tests, 2 passing subtests, and 2 failing
prospective-write gate tests. These failures must not be waived or have their
expected rule activation changed. Shared nested-output reference support has
been proposed to the user; it is not implemented at this checkpoint. This is
an extension beyond the earlier workflow-only cleanup, not a new aggregation
mode or an LSP scoring change.

Full non-live checkpoint after the scope fix: **2,864 passed, 199 subtests
passed, 4 existing skips, 2 failed**. Breakdown: MCP 1,216; flow engine 933
passed and the same 2 gate failures; harness/Stop/dispatch 174; scripts 253;
Apple-build/skill scripts 288. MCP and flow-engine semantic integration checks
ran with approved access to the installed SourceKit service. The initial
sandboxed flow run could not complete semantic queries; those additional
failures disappeared with SourceKit access. No failing assertion was weakened.

## Method-call return contract fix — 2026-10-19

The real gate's `cache.object(forKey: key as NSString) as? Data` inspection was
unavailable because the adapter only resolved identifier operands. The installed
LSP resolves the called method, but its type-definition response does not resolve
the call's returned type. The approved fix extends semantic binding, not LSP's
rule semantics or the definition of external ownership.

- [x] Add failing semantic tests for the exact SDK cache expression and a
  project-owned method returning an interface; keep the target unwritten.
- [x] Verify installed native cursor requests expose a substituted return-type
  semantic reference, and that querying its identity resolves independent origin.
- [x] Reuse the active LSP's compiler settings and same-toolchain native library
  in a lazy isolated worker, with existing framed transport and bounded cleanup.
- [x] Keep application data typed and reuse the shared syntax-parser contract,
  symbol decoder and ownership resolver. Do not add a new model-facing tool.
- [x] Confirm exact callee and returned-type identities before accepting evidence.
  Retain unavailable outcomes for unsupported shapes and provider failures.
- [x] Test SDK-generic methods returning owned types, overload selection,
  one shared native worker, no worker for identifiers, and cleanup on failure.
- [x] Test the real bundled LSP operation before aggregate classification,
  scoring after submission and replay without repeating semantic analysis.
- [x] Strengthen the real write-gate test to require verified cache-call evidence
  and measured LSP-1, retaining its existing LSP-3 severe assertion.
- [x] Complete all non-live suites and locked Codex/Claude LSP and write-gate checks.

Focused validation: semantic provenance **9 passed**; document lifecycle
**5 passed**; return-reference decoding **4 passed, 10 subtests**; native transport
**3 passed**; return-contract selection **6 passed**; call-position selection
**2 passed, 10 subtests**; real LSP integration **11 passed, 2 subtests**.
The first semantic cases and new adapter tests failed before implementation.
No source fixture, workflow prompt, scoring threshold or expected rule score changed.

Final non-live suite after the test-evidence correction below:

| Suite | Passed | Subtests | Skipped |
|---|---:|---:|---:|
| `tests/mcp-server --ignore-glob='*_live.py'` | 1,236 | 115 | 4 |
| `tests/harness/flow_engine --ignore-glob='*_live.py'` | 942 | 45 | 0 |
| `tests/harness/tests tests/hooks/stop tests/mcp/hook_dispatch` | 181 | 2 | 0 |
| `scripts/tests` | 253 | 66 | 0 |
| `mcp-server/build/apple/tests skills` | 288 | 0 | 0 |
| Total | **2,900** | **228** | **4** |

Each group ran with `/opt/homebrew/bin/python3.12 -m pytest ... -q`.
The four skips are existing abstract fixtures. SourceKit integration tests ran
with approved access to the installed toolchain, not substituted mock responses.

The implementation deliberately does not use hover prose, type-name allowlists
or called-method ownership as evidence for return ownership. Missing native
tooling/settings remain explicit unavailable reasons; no packages are installed,
projects built or global indexes requested. Structured compiler XML is decoded
only at the native boundary; unsupported composite and opaque types stay unknown.

### Live validation and test-evidence correction

The ten-case run exercised `test_lsp_validation_live.py`,
`test_lsp_type_inspection_live.py`, `test_lsp_repository_relationship_live.py`,
`test_workflow_catalog_e2e_live.py` and `test_solid_gate_on_write_live.py`, with
locked Codex Terra and Claude Opus profiles. Initial result: **9 passed, 1 failed
in 875.50 seconds**. The remaining failure was not ignored:

- Codex's relationship run returned the locked 0/1/0/0 metrics, performed the
  selected declaration reading and then classified the new guard. It had no
  failed or unanswered tool calls and no failed workflow attempts.
- The shared test incorrectly prohibited the reviewed source in every tool
  response, including an explicitly requested file read of the same file.
- The existing transcript reader now correlates `flow_start`/`flow_next` outputs
  separately. The no-source-repetition assertion applies to those responses;
  instructed source reads remain permitted. Two new tests first failed and then
  passed, proving both allowed reads and detection of source repeated by MCP.
- Rechecking the saved run passed. A fresh Codex relationship live rerun also
  passed in **59.36 seconds**, with the same fixture, scores and step assertions.
  All ten live cases therefore passed across these runs. Production workflows
  and metric expectations were not changed for the test correction.

Both real write gates completed and denied the known violations. Their cache-call
inspection resolved the called method `c:objc(cs)NSCache(im)objectForKey:` and its
return contract `s:s9AnyObjecta` as distinct semantic identities. No inspection
limitations remained; LSP-1 was measured as zero and LSP-3 remained one SEVERE
violation. Neither gate event log recorded a failed step attempt. The separate
aggregate inspection fixture retained its deliberately unresolved binding and
unavailable LSP-1 coverage on both models.

Canonical user-root gate runs:

- Codex: `/Users/crowea/.solid-coder/-private-var-folders-42-g1w_3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-xha0gydg/runs/subagents/78cd79bd0da2443c836bc2088d404a42/`
- Claude: `/Users/crowea/.solid-coder/-private-var-folders-42-g1w_3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-4rxdsag0/runs/subagents/dbf9ce6386be49a3bd1e1034f018d20f/`

Preserved test copies (including hook input/output and model profile):

- Codex: `.solid-coder/.artifacts/test/codex/e2e/gate/solid-gate-on-write/20261019T220848Z-a4305a5b/`
- Claude: `.solid-coder/.artifacts/test/claude/e2e/gate/solid-gate-on-write/20261019T221053Z-3ab3ab1b/`
- Original Codex relationship evidence: `.solid-coder/.artifacts/test/codex/e2e/review/lsp-relationships/20261019T220541Z-f9a36395/`
- Successful fresh rerun: `.solid-coder/.artifacts/test/codex/e2e/review/lsp-relationships/20261019T221550Z-4a231c79/`

The older failing checkpoints above are historical, superseded by these results.
This fix does not address the separate malformed-JavaScript submission issue or
claim broader semantic support beyond the explicit return-contract scope.
