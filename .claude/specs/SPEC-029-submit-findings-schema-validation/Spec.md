---
number: SPEC-029
feature: submit_findings schema validation and batch gate findings
type: feature
status: done
blocked-by: []
blocking: [SPEC-036]
---

# submit_findings Schema Validation (pipeline + gate)

## Context

Two callers need enforcement:

1. **`apply-principle-review`** (pipeline) — one principle per run, returns raw JSON text today
2. **Gate health check** (`hc_checker.py`) — all principles in one subprocess, returns raw JSON today

Root cause: LLM can skip required metric fields, produce wrong types, or return plain text.
Fix: route both through `submit_findings`, which validates against `review/output.schema.json`.

---

## Part A — Schema validation inside submit_findings

### `mcp-server/lib/gateway_tools.py`

The existing `validate_json()` function in `skills/prepare-review-input/scripts/validate-output.py`
already does jsonschema validation. Inline the jsonschema call in `SubmitOrchestrator.orchestrate()`
before the scoring step:

```python
# Resolve schema path from the principle folder (ScoringHandler already resolves it)
schema_path = principle_folder / "review" / "output.schema.json"
if schema_path.exists():
    try:
        jsonschema.validate(partial_output, json.loads(schema_path.read_text()))
    except jsonschema.ValidationError as e:
        return {"error": f"Schema violation for {principle}: {e.message}"}
```

Invalid → return error, nothing written. Valid → existing score → write → summarise.

---

## Part B — apply-principle-review (one call, one principle)

### `skills/apply-principle-review/SKILL.md`

Output step: call `mcp__plugin_solid-coder_pipeline__submit_findings` with the completed
`partial_output` (metrics filled, scoring/findings absent) and the `output-path` received
as input. If tool returns `{"error": ...}`, fix the field and call again.

### `agents/apply-principle-review-agent.md`

Confirm `mcp__plugin_solid-coder_pipeline__submit_findings` is in allowed tools.

---

## Part C — Gate health check (one batch call, all principles)

The gate LLM reviews ALL principles in one pass. Makes **ONE** `submit_batch_findings` call.

### New tool: `submit_batch_findings` in `mcp-server/pipeline/server.py`

```python
@server.tool(
    name="submit_batch_findings",
    description="Submit health check findings for all reviewed principles in one call.",
    input_schema={
        "type": "object",
        "properties": {
            "output_dir": {"type": "string"},
            "submissions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "partial_output": {"type": "object"},
                        "output_path": {"type": "string"}
                    },
                    "required": ["partial_output", "output_path"]
                }
            }
        },
        "required": ["output_dir", "submissions"]
    }
)
def submit_batch_findings(output_dir, submissions):
    for item in submissions:
        r = _gw_pipeline.submit_findings(item["partial_output"], item["output_path"])
        if "error" in r:
            return {"error": r["error"], "failed_at": item["partial_output"].get("principle")}
    return {"ok": True, "submitted": len(submissions)}
```

### `hooks/hc_checker.py` — HealthPromptBuilder

Add `output_dir` to `build()` and pass to `workflow.md` as `{output_dir}`.
Derived: `output_dir = str(Path.home() / ".solid-coder" / "gate" / parent_session_id)`

### `mcp-server/prompts/health-check/workflow.md` — Step 4

```xml
<step id="4" name="submit" required="true">
  After completing all detection and fix-guidance steps, call
  mcp__pipeline__submit_batch_findings ONCE with:
    - output_dir: {output_dir}
    - submissions: one entry per active principle, each with:
        - partial_output: your complete analysis for that principle
        - output_path: {output_dir}/{principle_agent_name}/review-output.json

  Include ALL principles you received detection instructions for.
  If the tool returns {"error": ...}, fix the named field and call again.
  Do NOT return any JSON text.
</step>
```

### `mcp-server/prompts/health-check/output-format.md`

Replace JSON return instructions with:
```
Do NOT return JSON text. Use submit_batch_findings (step 4) for all output.
```

### `hooks/hc_checker.py` — LLMReviewer.review()

After `runner.run()` completes, read from `output_dir`:
1. Scan for `*/review-output.json` files
2. Aggregate via `ScoredResultConverter.violations_from_scored()`
3. Zero files → raise `RuntimeError("LLM did not call submit_batch_findings")`

### `hooks/hc_checker_factory.py`

Add `mcp__pipeline__submit_batch_findings` to `_ALLOWED_TOOLS`.

---

## What This Fixes

| Problem | Fix |
|---|---|
| LLM skips required metric fields | Schema validation rejects → LLM must retry |
| LLM skips principles silently | Batch requires all principles in one call |
| Raw text parsing brittleness | No text parsing — gate reads submitted files |
| Model reliability | Forced tool use; JSON text path removed |
| Session visibility | Tool call appears in session panel |

## Files to Modify

| File | Change |
|---|---|
| `mcp-server/lib/gateway_tools.py` | Add schema validation in `SubmitOrchestrator.orchestrate()` |
| `mcp-server/pipeline/server.py` | Add `submit_batch_findings` tool |
| `skills/apply-principle-review/SKILL.md` | Output step → call `submit_findings` |
| `agents/apply-principle-review-agent.md` | Confirm `submit_findings` in allowed tools |
| `hooks/hc_checker.py` | `HealthPromptBuilder` adds `output_dir`; `LLMReviewer` reads files |
| `hooks/hc_checker_factory.py` | Add `mcp__pipeline__submit_batch_findings` to allowed tools |
| `mcp-server/prompts/health-check/workflow.md` | Add step 4 |
| `mcp-server/prompts/health-check/output-format.md` | Remove JSON return |

## Reusing validate_json

`skills/prepare-review-input/scripts/validate-output.py` already has `validate_json(path, schema_path)`.
`pipeline/server.py` already imports it as `validate_output_mod`. Inline the jsonschema call
in `SubmitOrchestrator` — no new validator class needed.

## TDD — Write Tests First

Tests are written before any implementation. All tests must be red before touching production code.

### `tests/mcp-server/test_submit_findings_validation.py` (new)

- `test_valid_srp_submission_passes()` — valid SRP partial_output → file written, summary returned
- `test_srp_missing_cohesion_groups_is_rejected()` — missing metrics.cohesion_groups → error, no file
- `test_srp_wrong_metric_type_is_rejected()` — verbs.count is string not int → error, no file
- `test_principle_with_no_schema_passes_through()` — custom principle, no schema → no validation error
- `test_empty_files_passes_validation()` — empty files array → accepted, all_compliant: true

### `tests/mcp-server/test_submit_batch_findings.py` (new)

- `test_batch_with_two_valid_principles()` — valid SRP + OCP → both files written
- `test_batch_fails_fast_on_first_invalid_schema()` — SRP valid, OCP wrong → error with failed_at
- `test_batch_with_empty_submissions_list()` — empty list → {ok: true, submitted: 0}

### `hooks/tests/test_hc_checker_batch.py` (new)

- `test_reviewer_reads_violations_from_output_dir()` — pre-populated output_dir → violations returned
- `test_reviewer_raises_when_no_files_found()` — empty output_dir → RuntimeError
- `test_reviewer_aggregates_findings_from_multiple_principles()` — SRP + DRY files → combined list

### Implementation order (TDD cycle)

1. Write all tests (red)
2. Part A: schema validation in SubmitOrchestrator → Part A tests green
3. Part C: submit_batch_findings tool → batch tests green
4. Part C: LLMReviewer reads from output_dir → hc_checker tests green
5. Part B + C: prompts + SKILL.md + allowed tools
