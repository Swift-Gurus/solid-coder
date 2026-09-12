---
number: SPEC-036
feature: bundled-solid-workflows
type: feature
status: in-progress
parent: SPEC-001
blocked-by: [SPEC-012, SPEC-027, SPEC-028, SPEC-029, SPEC-031, SPEC-034, SPEC-035, SPEC-037, SPEC-039, SPEC-040, SPEC-041, SPEC-042, SPEC-043, SPEC-044, SPEC-045]
blocking: []
---

# Bundled SOLID Workflows and Gate-on-Write Migration

## Description

Ship three stable workflows—`solid-review`, `solid-gate-on-write`, and `solid-refactor`—through the workflow package system. `solid-refactor` composes `solid-review`. The pre-write code-quality gate stops constructing and sending its own aggregated health-check prompt; it deterministically prepares the candidate code as normalized review input, starts `solid-gate-on-write` as an isolated run, and drives that run through the configured LLM backend until the workflow returns an allow/deny result.

## Input / Output

| Workflow | Input | Output |
|---|---|---|
| `solid-review` | A typed working-tree, file, files, folder, Git-range/PR, buffer, or code-block target | Schema-validated per-rule measurements, deterministic findings, and review artifacts |
| `solid-gate-on-write` | Prospective post-write buffer, required target path, and session metadata | Deterministic `allow` or `deny` result with structured violations and fix guidance |
| `solid-refactor` | The same review target plus refactor limits | Initial `solid-review` results, synthesized fixes, applied changes, verification, and residual findings |

## User Stories

### US-1: Run the bundled review workflow

As a developer, I want one stable `solid-review` workflow so review behavior is reusable from a direct command, another workflow, or an integration.

**Acceptance Criteria:**
- The plugin distributes a package whose declared ID is `solid-review`.
- It accepts the sealed review-target contract from SPEC-041 and normalizes every variant into one review-input model before rule selection.
- It reviews SRP, OCP, LSP, ISP, and DRY using explicit metric procedures and schema-validated outputs; server-side scoring remains authoritative.
- Each required metric is represented by an independently completable/validatable step or subflow output, so a model cannot silently omit a metric in a single holistic response.
- The reviewed source is supplied to the configured model once as session context before workflow execution. Normalized files, units, source snapshots, applicability data, tags, and evidence remain MCP-owned execution state used for deterministic rule selection and validation.
- Model-facing rule prompts contain authored detection instructions, a stable file or unit identity, and the required output contract. They must not serialize normalized review objects or repeat source text already present in the model session.
- Dependent rule steps may instruct the model to use analysis it previously submitted, while MCP resolves and validates the typed dependency internally. Prior typed outputs must not be rendered back into later model prompts.
- Per-principle results are aggregated only after every required principle output is present and valid.
- A client package declaring `id: solid-review` is rejected as a catalog collision; bundled workflow behavior cannot be replaced implicitly.

### US-2: Run the write gate as a workflow

As a developer, when an agent proposes a source write, I want the existing write hook to execute `solid-gate-on-write` instead of sending a separate hand-built review prompt.

**Acceptance Criteria:**
- The existing content simulator produces the exact prospective post-write content before any LLM call.
- Deterministic preparation constructs the SPEC-041 `buffer` target using the exact target path and prospective content. Exact extension comes from the path; units and tags come from SPEC-040 source analysis.
- A gate buffer always uses the text-backed target variant, including edits to existing files. Its absolute virtual path is required for identity and extension detection but is never read as the review source, so a destination that does not exist yet is reviewed without a temporary pre-write file.
- A multi-file patch preserves every prospective post-patch file snapshot in one server-owned source context. Each file is reviewed from its own in-memory content, while DRY can search prospective siblings and cross-file candidates before any write is authorized.
- The hook calls the same typed review-target normalization application service used by `solid-review`, directly rather than opening an MCP loopback connection.
- The hook starts an isolated `solid-gate-on-write` run before starting the child LLM session.
- The flow engine owns the isolated run's artifact directory under the project's user-level `.solid-coder` storage. The bootstrap prompt, workflow prompts, and model-facing MCP tool schemas neither expose nor accept an `output_dir` or other caller-selected persistence path.
- Search, measurement, scoring, and fix artifacts resolve from server-owned run context and remain within that run's artifact tree. Missing, stale, or mismatched run context fails closed; it is never treated as a non-gate invocation and never falls back to the process working directory or repository root.
- Concurrent gate runs bind their MCP operations to distinct run contexts, so one run cannot read, overwrite, or redirect another run's artifacts.
- The child session's bootstrap prompt is a generic flow envelope containing the prepared code once, the `run_id`, and the initial ready-step instructions returned by the flow engine.
- `solid-gate-on-write` composes the canonical `solid-file-review-aggregate` workflow. Applicable rule steps retain their individual identities, schemas, scoring, retries, replay, and audit events while the flow engine presents compatible ready work through aggregate execution and combined prompt presentation; the gate must not fall back to one child-model turn per granular metric step.
- The child session advances only through `flow_next(run_id=...)`; every step output is schema-validated and recorded before the next instruction is returned.
- The old `HealthPromptBuilder` detection/workflow prompt path is removed from gate execution; there is no direct-prompt fallback that can produce different review semantics.
- `code_review_on_write_enabled = false` still bypasses the gate. When enabled, flow failure, timeout, malformed output, or an unfinished run fails closed with a diagnostic and leaves run evidence available.

### US-3: Reuse review from refactor

As a developer, I want `solid-refactor` to invoke `solid-review` rather than carry a second copy of review instructions.

**Acceptance Criteria:**
- The plugin distributes a package whose declared ID is `solid-refactor`.
- Its initial analysis is an aliased workflow-ID include of `solid-review`.
- It consumes the included review group's structured outputs to synthesize and apply fixes.
- Its verification review invokes `solid-review` again; it does not copy principle detection prompts into the refactor package.
- The run terminates with residual findings when the configured attempt/iteration cap is exhausted.

### US-4: Keep gate and review measurements comparable

As a maintainer, I want the gate and full review paths to share the same principle measurement workflows so accuracy comparisons remain apples-to-apples.

**Acceptance Criteria:**
- `solid-review` and `solid-gate-on-write` compose the same plugin-private per-principle measurement packages.
- Principle detection procedures have one authoritative source used to generate or load workflow instruction content; handwritten copies in gate prompt files are forbidden.
- The same prepared buffer run produces the same required metric keys and deterministic scores whether invoked through the gate workflow or through `solid-review`.
- Run evidence captures model/backend profile, elapsed time, tool-reported usage when available, per-step outputs, retry counts, and terminal status.
- Accuracy, token, and duration tests report each completed run independently and exclude cancelled/incomplete runs explicitly.

## Workflow Packaging

```text
{plugin}/workflows/
  review/
    bundles/
      solid-review/workflow.yaml
      solid-files-review/workflow.yaml
      solid-file-review/workflow.yaml
      solid-file-review-aggregate/workflow.yaml
      solid-unit-review/workflow.yaml
    rules/
      srp/workflow.yaml
      ocp/workflow.yaml
      lsp/workflow.yaml
      isp/workflow.yaml
      dry/workflow.yaml
      code-smells/workflow.yaml
      frontmatter/workflow.yaml
  gates/solid-gate-on-write/workflow.yaml
  refactor/solid-refactor/workflow.yaml
```

- The public IDs are `solid-review`, `solid-gate-on-write`, and `solid-refactor`.
- Review bundles and rule packages are reusable implementation details and still have explicit IDs for validated composition.
- `review/rules` and `review/bundles` are organizational paths only. Catalog enrollment comes from the root `rule:` marker and execution remains explicit.
- The ordinary review profile runs SRP, OCP, LSP, ISP, and DRY. The code/write profile additionally preserves the existing code-smells and frontmatter checks through typed workflow conditions.
- Public callers never address installed package paths.

## Gate Execution Sequence

```mermaid
sequenceDiagram
  participant Hook as Pre-write hook
  participant Prep as Review target normalizer
  participant Flow as Flow engine
  participant LLM as Configured LLM session
  Hook->>Prep: typed buffer target with prospective content + path
  Prep-->>Hook: normalized buffer review input
  Hook->>Flow: start solid-gate-on-write, isolated
  Flow-->>Hook: run_id + initial instructions
  Hook->>LLM: code once + run_id + initial instructions
  loop Until terminal
    LLM->>Flow: flow_next(outputs, run_id)
    Flow-->>LLM: validated next instructions or terminal result
  end
  LLM-->>Hook: terminal result
  Hook-->>Hook: allow or block original write
```

## Temporary Test-Code Gate Workaround

- This repository currently excludes `tests/**` from the pre-write health-check gate. This is a temporary development workaround because the current prompt-based gate does not classify test support, mocks, fixtures, and test-only composition reliably, and its authored exception handling can produce false-positive SOLID findings for those units.
- The blanket test-tree exclusion is not the target behavior for `solid-gate-on-write`. The workflow-based gate must identify test code through deterministic path/source tags and apply explicit test-code or test-double rule exceptions with recorded reasoning and evidence.
- Once test-code classification and auditable exceptions are covered by deterministic and live gate tests, the blanket `tests/**` exclusion must be narrowed or removed.
- No production source path may be added to the exclusion list to suppress a finding. Production exceptions must remain explicit rule decisions recorded in the workflow audit trail.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Upstream | SPEC-035 Workflow Packages | Provides stable IDs, bundled discovery, collision protection, and composition |
| Upstream | SPEC-034 Static SRP Validation Flow | Supplies the measured evidence that stepwise SRP instructions are repeatable |
| Upstream | SPEC-012 and SPEC-029 | Provide deterministic scoring, batch submission, and fix submission |
| Upstream | SPEC-028 | Provides isolated configured-backend sessions and explicit run IDs |
| Replaces | Direct pre-write health-check prompt assembly | Gate execution becomes a flow run |
| Upstream | SPEC-040 Source MCP Namespace | Supplies deterministic change/range collection, exact extension, units, tags, and evidence |
| Upstream | SPEC-041 Review Target Normalization | Converges working tree, file(s), folder, Git range/PR, buffer, and code-block requests |

## Test Plan

Current implementation boundary: `solid-review`, reusable `solid-file-review`, and `solid-gate-on-write` are packaged and executable. The production pre-write hook now starts the gate workflow instead of the legacy hand-built review prompt. Gate preparation always supplies the exact prospective text with an absolute virtual path, keeps new destinations absent, ignores stale destination content, and carries the complete ordered multi-file patch snapshot collection into each isolated per-file review. `solid-review` statically composes `solid-file-review`; the ordinary file workflow invokes internal `review.prepare`, fans out normalized units, expands `rules: all`, applies the singular project review policy before rule materialization, materializes file-scoped rules once, and supplies the source context required by DRY. `solid-gate-on-write` composes `solid-file-review-aggregate`, which performs the same preparation and canonical dynamic rule expansion while aggregating compatible ready rule steps into combined model-facing phases without changing their validation, scoring, retry, replay, or audit identities. The experimental single-prompt bundle remains available for controlled prompt-shape comparisons. General multi-file target normalization for conversational review, nested dynamic file fan-out, rule-authored fix guidance, `solid-refactor`, removal of the temporary test-path exclusion, and the locked legacy-vs-workflow benchmark remain open work.

- Validate every bundled package and every workflow-ID include without starting an LLM.
- Normalize and run working-tree, file, files, folder, Git-range/PR, buffer, and code-block targets through the same `solid-review` package.
- Run `solid-review` against the established SRP fixture and assert every step/output pair plus final score.
- Run a five-principle fixture through `solid-review` and prove no principle or required metric is missing.
- Run `solid-gate-on-write` through the real pre-write hook for compliant and violating buffers; assert allow/deny, run completion, and recorded evidence.
- Assert every model-facing rule step returned by `solid-gate-on-write` belongs to the aggregate execution boundary and that the rendered turn contains one combined submission contract for all compatible ready steps rather than one prompt per metric.
- Run `solid-gate-on-write` against a new absolute destination path that does not exist and assert the exact supplied buffer is parsed, tagged, reviewed, and audited without creating or reading the destination before the gate allows it.
- Run an edit whose on-disk file contains stale content and assert the gate reviews only the simulated prospective text; run a multi-file patch and assert every prospective snapshot is available to DRY while no file is modified before the aggregate allow decision.
- Run test-support, mock, fixture, and test-only composition buffers through `solid-gate-on-write`; assert deterministic test tags, applicable exceptions, and persisted reasoning/evidence before removing the temporary `tests/**` exclusion.
- Assert the gate invokes no direct `HealthPromptBuilder` review path.
- Assert prepared candidate code appears exactly once in the initial model message and never appears in `flow_start` or `flow_next` results.
- Assert every model-facing rule step identifies its selected file/unit without rendering normalized review objects, applicability metadata, tags, source snapshots, or prior typed outputs.
- Force malformed output, timeout, and runner failure; assert fail-closed behavior and preserved run diagnostics.
- Assert model-facing gate tools expose no persistence-path parameter, every generated search/finding/fix artifact remains beneath the engine-owned run directory, and no artifact is written beneath the repository working directory.
- Run two gate workflows concurrently and assert each MCP operation resolves only its bound run context; missing, stale, and cross-run context identifiers are rejected without writing artifacts.
- Attempt to publish a client package under each bundled public ID and prove catalog construction rejects every collision.
- Run `solid-refactor` and assert both initial and verification review groups resolve from `solid-review`.
- Repeat the same fixed fixture/model profile through gate and review workflows; compare metric accuracy, tokens, and elapsed time from complete runs.
- Every accuracy, token, cost, and elapsed-time comparison must enter through the real public review boundary used in production. Workflow measurements start `solid-review`, supply a normalized target, and select the tested rule through project policy; legacy measurements call the real principle-scoped health checker. Direct child-rule starts and directly addressed experimental workflows are protocol diagnostics only and are invalid as end-to-end comparison evidence.
- Defer the one-principle phased-versus-aggregated prompt-shape experiment until both prompt shapes can be selected behind the same `solid-review` entry chain with identical normalization, policy, MCP registration, output limits, artifact capture, and terminal scoring. Both arms must use the same isolated fixture, locked observations, model profile, and scoring authority.
- Persist every comparison run under the established test artifact root with model profile, target hash, effective workflow/rule hashes, expected and observed metrics, applicability and exception decisions, retry/error state, elapsed time, token usage, reported cost availability/value, transcript, flow events, and normalized review results.

### Invalid Comparison Evidence Requiring a Controlled Rerun

The August 22 workflow smoke run `20260822T231121Z-319dca59` and legacy smoke run `20260822T232230Z-6b4f0b78` are invalid benchmark evidence and must not support accuracy, token, cost, or speed conclusions. Their reviewed fixture remained inside this repository, so DRY searched the solid-coder working tree instead of a controlled comparison project. The workflow run additionally returned 40 DRY candidate-classification instances in one oversized response; the Codex tool wrapper truncated that response and the model fabricated uniform classifications for candidates it had not inspected. The legacy run also searched the solid-coder working tree, although it used the legacy single-search path rather than the workflow's candidate-per-instance fan-out.

Before rerunning the comparison:

- Create one controlled temporary project outside the solid-coder source corpus, place the reviewed target under its production-source folder, and seed only the intended DRY candidate files.
- Pass that same project root, exact source buffer, model/profile, rule set, and expected observations to the real legacy health-check entry point and the real bundled review workflow.
- Capture and hash the actual model-facing legacy prompt from the transcript; do not substitute a test-constructed prompt or raw rule-file hashes.
- Make `flow_start` and `flow_next` preserve one complete, untruncated ready-step response. Do not hide oversized responses through pagination or candidate chunking.
- Ensure generated Codex live-test configuration carries the same output limit required by the complete `flow_start` and `flow_next` response contract.
- Restrict DRY discovery to eligible source/code units; documentation, specifications, caches, authored rules, workflow definitions, and skill instructions must not become reuse candidates.
- Present DRY search candidates to the LLM as stable IDs, descriptions, and absolute inspection paths. The LLM selects promising IDs from those summaries, reads the selected files with its own file-reading tool, and submits one evidenced reuse and duplication classification for every selected ID. MCP must not load candidate source into the prompt. It validates exact selected-candidate coverage and rejects missing, duplicate, unknown, or fabricated classifications.
- Preserve `NOT_SUITABLE` and `NOT_DUPLICATE` outcomes for selected candidates whose source disproves the summary-level match, and prevent protocol/conformer relationships without duplicated implementation from being counted as duplication.
- Keep the 20-candidate search policy unchanged until candidate eligibility and classification semantics are corrected.
- Carry prerequisite analysis through typed step outputs: OCP dependency analysis must feed every dependent OCP metric, ISP conformer evidence must feed coverage/cohesion metrics, and LSP trigger plus SRP applicability decisions must feed their dependent steps instead of being independently re-inferred.
- Repair the malformed legacy OCP prompt separately from the workflow comparison so legacy prompt defects remain visible and attributable.
- Assert the exact searched project root, discovered file count, candidate paths, candidate count, classification count, and final normalized observations for both paths.
- Report review-only and full gate/fix costs separately, with per-turn token and duration breakdowns, so unlike stages are not compared. Run one valid smoke before repeated measurements and lock expected results before calculating accuracy.

## Definition of Done

- [ ] All three public workflow packages are shipped and start by stable ID.
- [ ] `solid-review` covers SRP, OCP, LSP, ISP, and DRY with complete validated metrics.
- [x] Gate-on-write uses `solid-gate-on-write`; direct health-review prompt execution is removed.
- [x] Gate artifacts are routed exclusively by server-owned flow-run context; model calls cannot select or redirect persistence paths.
- [x] Candidate-write preparation is deterministic and shared with the typed review-target boundary.
- [x] New and existing destination paths are reviewed from prospective in-memory text with required virtual identity; gate preparation never rereads stale or nonexistent destination content and never creates a pre-write temporary source file.
- [x] Multi-file patches preserve one immutable prospective snapshot collection across every isolated per-file review and produce one aggregate fail-closed gate decision before any write is authorized.
- [ ] Test code is classified deterministically, test-specific exceptions are auditable, and the temporary blanket `tests/**` gate exclusion is narrowed or removed without excluding production code.
- [ ] `solid-refactor` includes `solid-review` for both initial and verification analysis.
- [ ] Client packages cannot override bundled workflow IDs; collisions fail with actionable diagnostics.
- [ ] Live gate/review/refactor tests and token/time/accuracy evidence pass on the locked model profile.
