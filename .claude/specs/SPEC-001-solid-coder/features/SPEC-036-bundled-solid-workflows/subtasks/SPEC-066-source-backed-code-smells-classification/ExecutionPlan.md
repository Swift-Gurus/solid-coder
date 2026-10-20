# SPEC-066 execution plan

## Sequence

1. Record the CS-2 counting scope decision; retain existing thresholds and legacy
   behavior. Reuse shared source analysis, operation binding, batching, and scoring.
   Decision confirmed: count independent implementation/contract boundaries;
   allow cohesive implemented contracts and file-confined supporting helpers.
   Consumed-only contracts and unrelated types remain separate. Declaration-site
   and extension-site conformance are equivalent; extensions do not add a type.
2. Write failing tests through the real source-analysis operation for nested
   declarations, enclosing scopes, modifiers, identity stability, comments and
   literals, file/buffer equivalence, and unsupported/partial analysis.
3. Extend the generic declaration inventory using the existing Swift syntax parse
   and traversal. Preserve the current top-level units used by other rules.
4. Write failing workflow tests for server-grounded classifications, exact candidate
   coverage, corrected submissions, exception filters, CS-2 grouping, and fixed
   exception binding. Reuse existing generic capabilities before adding any shared
   operation or result-binding contract.
   Cover multiple cohesive implemented contracts, protocol-only files, injected
   dependency contracts, private versus non-private helpers, unrelated private
   implementations, extra conformers, and unresolved extension targets. Do not
   let a shared contract merge multiple non-exempt concrete implementations.
5. Update the real Code Smells workflow to classify judgments only, with concise
   candidate identities and source already in context. Keep all scoring in YAML/MCP.
6. Validate included aggregate execution, pending partial submissions, replay, and
   final result identity. Retain the original fixture's locked 1 / 2 / 1 values.
7. Run all non-live test groups. Then run Codex and Claude Code Smells plus the
   existing flow-engine live checks. Do not run a local model.
8. Record evidence, update the spec and related bug status, and report remaining
   limitations. Do not commit or bump the version without a separate request.

## Working constraints

- One file per patch; validate that file before moving to another.
- Tests mirror production folders under tests/mcp-server and tests/harness.
- Reuse SourceSyntaxParsing, existing typed source facts, node traversal, bounded
  relationships, and collection identity coverage instead of duplicate interfaces.
- Keep syntax extraction in source/analysis, never in the rule-specific scorer.
- Shared operations contain no CS IDs, exception policy, or severity bands.
- All source buffers remain server-owned; model instructions do not retransmit them.
- Follow the health gate, and do not change production exclusions or model settings.

## Evidence

- Initial inspection: the Swift inventory parses one tree but exports only
  top-level units and direct members. Local types have no shared scope inventory.
- Initial inspection: the current rule takes ungrounded model-created observations
  and asks a second prompt to return a fixed false whole-rule exception.
- Initial inspection: the rule result collector requires a completed exception
  observation; deterministic replacement must preserve this audited contract.
- Spec validation: structural sections are present; the user confirmed CS-2's
  scope on 2026-10-20. Final completion evidence is recorded below.
  Scope-measurement agents are intentionally not run, per the user's instruction.
- Shared inventory: the first eight tests failed before implementation. The
  completed inventory now has fourteen passing focused cases for nested scopes,
  modifiers, unique identities, single-tree parsing, serialization, prospective
  buffers, incomplete/unsupported source, file-confined visibility, and the
  distinction between extension conformance and consumed dependency contracts.
- Policy-source validation after confirmation: 40 tests passed across scoped
  declarations, declaration signatures, and bounded relationship resolution.
  Existing conformance tests were reused. These verify structural facts; final
  CS-2 grouping and scoring are covered by the later workflow checks below.
- Existing source member/signature/relationship validation: 79 tests passed.
- MCP test groups: 1,266 passed, four skipped, 115 subtests passed. This run
  started before the last four inventory tests were added; those four also passed
  in the twelve-case focused run. This is not the complete non-live suite or
  live-model validation.
- The bundled Code Smells workflow now performs source analysis and declaration
  selection before one classification assignment. The original legacy reference
  instructions and health-check mode setting remain unchanged.
- Classification binding reuses exact collection identity coverage and bounded
  relationship resolution. Missing IDs reopen only the affected classifier and
  require one complete replacement collection. Accepted sibling assignments and
  completed source operations survive retry/replay.
- The shared `source.analyze_text` adapter accepts flat text/path bindings and
  delegates to the existing analyzer. `source.select_declarations` accepts authored
  kinds/scopes/modifiers. `source.bind_declaration_classifications` attaches
  authoritative source facts to complete evidenced judgments. Policy remains in
  YAML, not these operations.
- Shared `rule.exception` supports an authored audited decision instead of a
  model step. It cannot coexist with a model exception or assessment step.
  Unavailable metrics are retained after source preparation, while wholly
  ineligible rules do not publish findings.
- Stop integration exposed missing source/review operation registrations in the
  Stop loader. It now uses the existing operation factories to reload the same
  contracts; Stop does not execute source operations or reclassify code.
- Focused checks: 19 authored boundary/scope scenarios pass; the original fixture
  remains 1 / 2 / 1. Aggregate tests prove partial acceptance, complete replacement
  after missing IDs, replay, one preparation per file, and Stop enforcement.
- The final binding guard rejects association with a callable-local type: related
  roots must be independent file-level types. Its new test failed before the fix
  and passed afterward; the final MCP and flow-engine suites include this guard.

## Final validation — 2026-10-20

- All non-live groups passed: 1,278 MCP tests, 996 flow-engine tests, 159
  harness/hook tests, 253 script tests, and 288 Apple/skill-script tests: **2,974
  passed, four existing skips, and 264 subtests passed**. The final MCP and
  flow-engine reruns include the Stop wiring and file-level association guard.
- The final live command ran `test_code_smells_validation_live.py` and
  `test_workflow_catalog_e2e_live.py`: **six passed in 204.76 seconds**.
- Both Code Smells fixtures ran through the real `solid-file-review-aggregate`
  bundle and bundled `code-smells` rule, not a copied test workflow. Codex used
  the locked `gpt-5.6-terra` profile; Claude used `claude-opus-4-5`. No local model
  was run. The catalog checks exercised nested workflow-ID resolution.

| Live case | Codex | Claude |
|---|---|---|
| Unchanged violation fixture | CS-1/2/3 = 1 / 2 / 1, all SEVERE | 1 / 2 / 1, all SEVERE |
| Cohesive direct/extension contracts and private helper | CS-1/2/3 = 0 / 1 / 0, all COMPLIANT | 0 / 1 / 0, all COMPLIANT |
| Nested workflow catalog | Passed | Passed |

Artifact directories below are relative to `.solid-coder/.artifacts/test/` and
retain model transcripts and flow-run evidence; rule runs include
`flow-run/results/review/result.json` with the values above:

- `codex/e2e/review/code-smells/20261020T215218Z-934e66e5`
- `claude/e2e/review/code-smells/20261020T215247Z-d05ac17c`
- `codex/e2e/review/code-smells-cohesive-boundary/20261020T215323Z-ffa2130b`
- `claude/e2e/review/code-smells-cohesive-boundary/20261020T215407Z-0888e5f9`
- `codex/e2e/flow-engine/workflow-catalog/20261020T215438Z-48edb7e8`
- `claude/e2e/flow-engine/workflow-catalog/20261020T215509Z-1afe9a1e`

This validates the scoped implementation and locked fixtures, not universal
semantic accuracy or a legacy/workflow benchmark. Swift is the initial structural
adapter; unsupported analysis remains explicitly unavailable. Legacy rules and
mode configuration are unchanged. No commit or version bump was performed.
