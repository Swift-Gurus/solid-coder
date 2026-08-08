# Handover: health-check → flow_engine migration — standalone SRP validation flow proven

**Current branch:** `feat/Na/session-scoped-run-lock`. SPEC-034 is implemented and verified locally; no changes have been pushed.

## Where this came from

Started from validating a user-supplied bug report about the Codex stop-hook (confirmed real: `mcp_tool_call_reader.py`'s `_collect_codex_rollout` only recognizes `payload.type == "function_call"`, but current Codex wraps MCP calls in `custom_tool_call` / `name: "exec"` / nested JS — verified against real rollout files on disk, not just theory). That investigation is explicitly **parked** — user said "forget codex for now." It's what motivated the next part, though: the fix's most robust form (server-side recording of tool calls, vs. reconstructing from a transcript) is structurally how the flow_engine already works, which led to the real topic of this session — migrating the health-check pipeline from one bundled per-file LLM prompt onto the flow_engine's workflow model.

## Decisions and verified result

1. **Full migration, not just health-check.** All five current `rule.md` consumers (review, code, planner, synth-impl, synth-fixes — see root `.claude/CLAUDE.md`'s mode table) will eventually move onto whatever new structured format replaces `rule.md`. This matters because it removes the "don't fork the source of truth" objection to converting to YAML — if everything moves, there's no second copy to drift.
2. **`rule.md` → YAML, not "extract from `.md` into flow steps."** Confirmed via `mcp-server/scoring/frontmatter_bands_provider.py` that the YAML frontmatter block (`bands:`) is *already* the sole machine-authoritative source for severity — read via plain `yaml.safe_load`, consumed by `PrincipleScorerProvider` → `SeverityScorer`, and **never shown to the LLM**. The body's `<definition id>` / `<detection id>` / `<exceptions>` tags are the model-facing content, assembled into the prompt by `mcp-server/rules/principle_content_builder.py:74-127`.
3. **The body's `<severity-bands id="...">` XML blocks are non-authoritative, but still exposed.** Deterministic scoring ignores them and reads only YAML frontmatter `bands:`. However, `PrincipleContentBuilder` still returns them in the structured `severity_bands` field and the `load_detection_rules` tool contract advertises that field, so they are not currently dead or invisible to the model. The migration should remove or deprecate that response field explicitly before deleting the XML blocks; only `bands:` + `definition`/`detection`/`exceptions` need to survive in the replacement source of truth.
4. **Target shape for the new format:** fold `definition`/`detection`/`exceptions` into the frontmatter itself, per metric ID, alongside the existing `bands:` — e.g.:
   ```yaml
   metrics:
     SRP-1:
       name: Verb Count
       definition: |
         List every distinct action (verb) the class performs...
       detection: |
         Count the distinct actions (verbs)...
       bands:
         verb_count: { minor: {greater_than_or_equal: 3}, severe: {greater_than: 5} }
   exceptions:
     - name: Facade / Coordinator
       ...
   ```
   Whether the file keeps a `.md`-with-YAML-frontmatter shape or becomes pure `.yaml` is still open — not decided, not urgent.
5. **Composition strategy for the *eventual* dynamic health-check flow: "generate flow YAML per run."** I.e., when the full system is built, the write-gate/health-check will compute active principles (same tag-matching as today) and programmatically assemble a run-scoped flow YAML (one `include:` per active principle), then `flow_start` against that generated file — rather than one static checked-in flow with conditional skipping. **This is not what's being built right now** — see "Immediate task" below, which is one static, hand-authored file.

## Confirmed facts about the flow_engine (read the actual code, not assumed)

- **Flow search paths**, in order (`mcp-server/harness/flow_search_path_resolver.py:30-42`):
  1. `$CLAUDE_PROJECT_DIR/.solid-coder/harness/flows/` (project-level — **this is where the test workflow goes**, not `.solid-coder/workflows/`)
  2. `<plugin>/mcp-server/harness/flows/` (plugin-bundled fallback)
- Existing working examples at `.solid-coder/harness/flows/e2e_test.yaml` and `e2e_review_group.yaml` — real syntax reference for steps, `outputs[].schema`, `depends_on`, `{{steps.<id>.outputs.<name>}}` interpolation, and the `include: <file> / as: <alias>` sub-flow pattern.
- `StepDef` fields (`mcp-server/harness/models.py:24-40`): `id`, `prompt`, `depends_on`, `outputs` (each with `schema` or `schema_file`), `for_each`, `type` (`agent`/`script`/`delegate`), `mode`, `prompt_file`, `command`, `timeout_seconds`, `max_attempts`.
- `flow_start(flow: str, params: dict, isolated: bool)` — confirmed `params` is interpolatable inside step prompts as `{{params.<key>}}` (`mcp-server/harness/run_context_builder.py:24` puts `params` straight into the render context, same mechanism as `{{steps...}}`). **This is how the target code-to-review gets fed into the flow** — pass it as a `flow_start` param, reference it in step prompts.
- `for_each` is **homogeneous fan-out only** — it repeats one step template once per item in a prior step's output list (validated by `for_each_reference_validator.py`). It cannot give SRP a different step graph than OCP. Heterogeneous per-principle step sets need `include:` (static) or programmatic flow construction (dynamic) — not `for_each`.
- Step outputs are recorded **server-side** the moment a step submits (`output_recorder.py`) — this is the actual robustness property that started this whole conversation. No transcript is ever re-parsed to determine what happened.
- Reference material for SRP specifically:
  - `references/principles/SRP/rule.md` — source to migrate. Has `bands:` for SRP-1 (`verb_count`), SRP-2 (`cohesion_groups`), SRP-3 (`stakeholder_count`), plus `<definition>`/`<detection>`/`<exceptions>` body blocks per ID.
  - `references/principles/SRP/review/output.schema.json` — current batch-submission schema; slice per-metric pieces from this for each step's `outputs[].schema`.
  - `references/principles/SRP/Examples/user-database-manager-violation.swift` — ready-made fixture, one method with 5 distinct responsibilities (URL construction, network call, response validation, JSON parsing, DB persistence) — good test input, no need to write a new violating sample.

## SPEC-034 proof result

- `.solid-coder/harness/flows/srp_validation.yaml` now defines three independent integer-valued metric steps and one dependent scoring step.
- The scoring step assembles the established partial-review document and instructs the driving session to call the existing deterministic `score_severity` MCP tool. The flow contains no severity thresholds.
- The gate exposed and fixed a real engine gap: the public flow contract documented `{{params.<key>}}`, but `ExpressionResolver` did not implement nested parameter lookup. It now resolves named run parameters and reports missing keys explicitly.
- Focused non-live flow-engine and scoring verification passed: **323 tests**.
- The real Claude plugin test passed in **53.42 seconds**: bare-name discovery succeeded, the flow reached terminal `done`, and deterministic scoring returned at least one SRP violation for `user-database-manager-violation.swift`.

## Next immediate spec

**Candidate SPEC-035 — structured principle rule source (SRP-first).** Define one machine-readable metric schema containing `definition`, `detection`, `bands`, and `exceptions`; migrate SRP to it; and make both prompt construction and deterministic scoring consume that same source. This removes the remaining copied detection prose before dynamic multi-principle flow generation is attempted. SPEC-035 has not been created yet.

## Open / unverified

- Whether `prompt_file`/`schema_file` *paths* (not just prompt string content) can be interpolated with a `for_each` item variable — came up in the broader design discussion, not needed for this prototype since it hand-authors fixed steps, but will matter once principle-selection becomes dynamic (decision #5).
- Cohesion-group measurement completed successfully in the live proof, but its accuracy still needs a broader fixture set before using this flow as a production replacement for the current review pipeline.
- No decision yet on whether the final `.md`-with-frontmatter vs pure-`.yaml` file shape (decision #4) applies to this SRP prototype or is deferred until the real migration.

## Explicitly not in scope right now

- The Codex stop-hook transcript-parsing bug (validated, but user said to set it aside).
- The dynamic "generate flow YAML per run based on active principles" composition system (decision #5) — this prototype is one static file.
- Migrating any other principle, or any of the other four `rule.md` consumers.
