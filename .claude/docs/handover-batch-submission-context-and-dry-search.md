# Handover: typed batch submission and DRY-search enforcement

**Status (2026-08-07):** The batch-submission context isolation and DRY-search enforcement repairs are production-wired and non-live verified. The historical investigation below is retained for rationale, but its paused-state instructions are superseded by this completion update.

## Completion update

- Raw MCP batch payloads are parsed immediately into immutable submission models.
- Batch preparation loads `hook-input.json` from the explicitly requested output directory and validates ownership without consulting the shared active pointer.
- Coverage validation, ordered fail-fast persistence, and response formatting use typed interfaces.
- Health-check submission is decorated with same-run DRY-search completion enforcement; ordinary review/refactor submission remains unaffected.
- `LegacyPrincipleSubmissionSubmitter` was removed. The production batch path now uses `PrincipleSubmissionSubmitter`, `PrincipleSubmissionScorer`, `ReviewUnitScorer`, and typed scoring results.
- Dictionary use in the new path is confined to MCP parsing and JSON rendering boundaries. Batch business interfaces accept immutable models and do not return anonymous tuples.
- `pipeline/server.py` now reuses the canonical gateway contract, flow-callables assembler, and pipeline-callables assembler instead of maintaining duplicate local protocols or callable builders.
- The stale Codex runner test now expects generated `mcp_config` instead of `codex_home=""`, matching the production test profile behavior.

### Verification

- Focused batch, context-isolation, DRY-enforcement, apply-patch fan-out, health-check, prompt, and pipeline-server tests: **154 passed**.
- Complete non-live sweep, run one root at a time because of the repository's known pytest import-name collisions: **1,650 passed, 4 skipped, 0 failed**.
- Live model/session tests were intentionally not run.

### Remaining separate follow-ups

- Specify and implement a simulated multi-file overlay if sibling files in one proposed patch must be compared with each other for new cross-file duplication.
- Decide whether structural DRY-2 search needs source identifiers or bodies in addition to frontmatter metadata and imports.

## Why the batch work started

The focused regression `tests/mcp-server/test_batch_submission_context_isolation.py` proves that `submit_batch_findings(output_dir, submissions)` still reads the shared `active-health-check` pointer. A submission can therefore use another worker's hook context instead of the `hook-input.json` owned by its requested `output_dir`.

Baseline before this branch:

- `test_batch_submission_context_isolation.py`: **1 failed** — persisted `/tmp/Foo.swift` instead of `/src/Expected.swift`.
- `test_submit_batch_findings.py`: **12 passed**.
- Full non-live sweep before the branch: **1,714 passed, 4 skipped, 2 failed**. The other failure was the stale Codex-runner expectation for `codex_home=""`; it is unrelated to batch submission.

## Accepted work already present

The worktree contains immutable models and protocol-backed collaborators for:

- requested-directory hook-context loading and ownership validation;
- MCP batch parsing with an accepted prefix plus the first labelled parse failure;
- immutable batch, principle, file, unit, metric, context, coverage, persistence, and response models;
- context application without anonymous tuple returns;
- typed coverage validation;
- ordered per-principle persistence results;
- a thin `BatchSubmissionHandler` facade over `BatchSubmissionCoordinator`;
- model-facing response formatting at the MCP output boundary.

Every accepted file was passed through the repository pre-write gate one file at a time and compiled before the next file was touched.

## Important design decisions

- Do not use dictionaries in batch business logic. Dictionaries are allowed only at external parsing or final MCP/JSON output boundaries.
- Do not return anonymous tuples. Use immutable explicit result models.
- Keep `BatchSubmissionHandler` as a thin facade; preparation, ordered persistence, and response formatting remain protocol-backed collaborators.
- Preserve ordered fail-fast behavior: valid principles before the first malformed principle are persisted, then the labelled error is returned.
- Load and validate hook context from the explicitly requested `output_dir`; never consult the shared global pointer in this path.
- Keep one-file edits until the multi-file gate behavior is fully trustworthy.

## Deliberately removed approach

`PartialReviewOutputSerializing -> dict` and its implementation were created, challenged, and deleted. They duplicated the existing serialization/persistence boundary and exposed a dictionary through a new protocol.

## Unresolved batch decision

`LegacyPrincipleSubmissionSubmitter` is a newly created compatibility adapter, not an existing implementation. It accepts typed models but internally rebuilds the legacy dictionary payload for `SubmitOrchestrator`.

The user correctly challenged this. There is no fully typed scorer/submission implementation yet. Before resuming, decide between:

1. remove the compatibility adapter and finish the typed validation/scoring/persistence path; or
2. explicitly accept the adapter as a temporary boundary and document its removal milestone.

Do not call the batch feature complete while this decision is unresolved.

## Exact continuation point after DRY is fixed

1. Remove or deliberately retain `LegacyPrincipleSubmissionSubmitter` according to the decision above.
2. Finish typed `PrincipleCoverageScope` configuration parsing; only its protocol exists so far.
3. Wire `McpBatchSubmissionParser`, `RequestedHookContextLoader`, `BatchSubmissionPreparer`, `OrderedBatchSubmissionPersister`, `McpBatchSubmissionResponseFormatter`, `BatchSubmissionCoordinator`, and `BatchSubmissionHandler` in `mcp-server/lib/gateway_tools.py`.
4. Make `ValidatedGatewayHandler` parse the raw MCP payload immediately and pass only `BatchSubmissionParseResult` into batch coordination.
5. Turn `test_batch_submission_context_isolation.py` green without changing its expectation.
6. Run `test_submit_batch_findings.py`, `test_submit_findings_validation.py`, batch context isolation, apply-patch fan-out, and health-check batch tests.
7. Run the complete non-live suite again.

## DRY-search defect that preempts this work

The health worker does call `search_codebase`, but the shared prompt asks for one aggregated query while the canonical MCP tool accepts `tags: string[]`. Codex therefore sends the whole sentence as one tag. The exact-word matcher scans the repository and returns zero candidates, after which the worker submits zero DRY metrics.

Confirmed in real Codex transcripts for `BatchSubmissionHandler` and both `BatchSubmissionCoordinator` attempts. A malformed one-element tag array returned zero matches across more than 1,400 files; the same terms split into individual tags returned candidates.

Additional gaps:

- no server-side requirement binds a successful DRY search to the same health-check `output_dir` before findings submission;
- the canonical search only considers frontmatter descriptions/tags/specs and imports, so structural DRY-2 searches are not covered;
- independently reviewed simulated files in one multi-file patch cannot see one another, so new cross-file duplication remains invisible.

## Completed DRY-search repair

- Canonical MCP search now accepts `query` plus health-check `output_dir`. Its retained `tags` input explicitly requires an array whose items are individual no-space terms; aggregated text in one tag is rejected.
- The embedded local runner exposes the same `query` plus `output_dir` contract and uses the same search coordinator and submission guard.
- The health workflow prompt provides the exact call shape and explicitly forbids passing the aggregated query as one `tags` entry.
- Successful search completion is recorded inside the same health output directory. A valid zero-result search records completion; malformed input and backend errors do not.
- Health-check batch submission is rejected with `dry_search_required` until completion proof exists. Non-health batch submission is unaffected.
- Every new `hook-input.json` generation clears any prior completion marker first. This prevents stale proof if the fallback `gate/<session-id>` directory is reused, including when debug mode retains artifacts.
- Focused DRY, prompt, local dispatcher, context, and health E2E validation: **63 passed**.
- Hooks-suite sweep: **522 passed, 20 failed**. Sixteen failures originate from the already-paused `ViolationResponseFormatter`/batch-factory import mismatch; four tests require write access under `~/.solid-coder` and were blocked by the test sandbox.

## Remaining DRY follow-up outside this repair

- Separately specify and implement the multi-file simulated-overlay requirement. The argument and evidence fix does not make sibling files in the same proposed patch visible to one another.
- Decide whether structural DRY-2 search requires indexing identifiers or source bodies in addition to frontmatter metadata and imports.

No batch production factory wiring or batch regression expectations were changed by the DRY-search repair. Resume them only through the continuation sequence above.
