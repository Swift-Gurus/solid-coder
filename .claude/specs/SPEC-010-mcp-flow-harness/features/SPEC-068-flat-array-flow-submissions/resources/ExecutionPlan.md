# SPEC-068 Execution Plan

## Constraints

Keep the real gate and flow-tool entry points on the same implementation. Keep the nested default, authored workflows, rule schemas, and scoring unchanged. Do not add a new batching engine or another public tool argument.

## Test-first sequence

1. Add failing configuration and submission tests for the flat envelope. Cover typed decoding, duplicate/unknown IDs, and mapping to original step instances without accepting partial envelopes.
2. Add engine integration cases for identical scoring, reordered records, partial acceptance, schema rejection followed by correction, and pending work after restart. Include an MCP-owned operation boundary.
3. Reuse the existing result-rendering and submission-mapping capabilities. Add flat presentation as an alternative; do not duplicate the output validation and completion path.
4. Persist the selected format and stable assignment addressing with the run. Exercise configuration changes between start and resume.
5. Wire the existing production configuration factories for both the gate's initial prompt and subsequent MCP calls. Cover text and JSON response selection so format flags cannot disagree.
6. Run all non-live suites sequentially. Keep newly failing behavior visible and fix it rather than excluding tests.
7. Run nested and flat variants through the existing locked Codex/Claude real gate tests with identical fixture and profiles. Preserve canonical audit locations, raw prompts/submissions, outcomes, tokens, and both engine/full-run timing. Do not enable the experiment by default.

## Existing components to reuse

- `StepOutputSubmissionMapping`, `BatchStepOutputSubmissionMapperFactory`, and `OutputSubmissionAdvancer`: address mapping followed by existing validation and recording.
- `StepRenderer` and its ready/sibling selectors: only present the active assignment group.
- `AggregateAssignmentCollector`, `AggregatePromptRenderer`, and the existing output schema builders: preserve authored instruction deduplication and schemas.
- `RunMetadataStore` and lifecycle factories: freeze the run contract without mutable global state.
- `FeatureFlagsConfig`, `FlowResultRendererCreator`, `FlowRunCreator`, and `WorkflowHealthCheckerFactory`: shared production configuration.
- Existing mirrored harness tests and `test_solid_gate_on_write_live.py`: no experiment-specific bundled workflow copies.

## Progress

- [x] Inspect the existing pipeline and capture SPEC-068.
- [x] Failing tests: configuration and engine/renderer tests failed before their implementation.
- [x] Implementation and focused checks: typed envelope, persisted IDs, unchanged metric fixture (2/2/2), partial recovery, stale/unpresented rejection, JSON presentation, and Stop blocking.
- [x] All non-live checks: 3,065 passed across the five suite groups, four existing skips; the subsequently added unpresented/stale-ID test and registration checks also pass (3,066 distinct tests total).
- [x] Controlled live measurements and conclusion: all four live checks passed; see [measurement report](Measurement-2026-10-21.md).

Live A/B completed through `test_solid_gate_on_write_live.py` and
`test_flat_submission_gate_live.py`, one nested and one flat run per backend.
Both use the original shared real-hook test base, fixture, assertions, and locked
profiles. The test now preserves full hook elapsed time as well as the canonical
audit copy. No rule workflows or schemas were modified.
