"""
solid-name: ScriptOutcomeEvaluator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Evaluates a script step's execution result into a step run outcome.
"""

from __future__ import annotations

import json

from harness.models import StepDef
from harness.output_validating import OutputValidating
from harness.script_execution_result import ScriptExecutionResult
from harness.script_outcome_evaluating import ScriptOutcomeEvaluating
from harness.step_run_outcome import StepRunOutcome


class ScriptOutcomeEvaluator(ScriptOutcomeEvaluating):

    def __init__(self, schema_validator: OutputValidating) -> None:
        self._schema_validator = schema_validator

    def evaluate(self, result: ScriptExecutionResult, step: StepDef) -> StepRunOutcome:
        if result.timed_out:
            return self._rejected(f"Step '{step.id}' timed out")
        if result.exit_code != 0:
            return self._rejected(result.stderr or f"Step '{step.id}' exited with code {result.exit_code}")

        try:
            outputs = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return self._rejected(f"Step '{step.id}' stdout is not valid JSON: {exc}")
        if not isinstance(outputs, dict):
            return self._rejected(f"Step '{step.id}' stdout must be a JSON object")

        errors = self._schema_errors(step, outputs)
        if errors:
            return self._rejected("; ".join(errors))
        return StepRunOutcome(awaiting_input=False, outputs=outputs)

    def _schema_errors(self, step: StepDef, outputs: dict) -> list[str]:
        errors: list[str] = []
        for spec in step.outputs:
            validation = self._schema_validator.validate(spec, outputs.get(spec.name))
            if not validation.ok:
                errors.extend(validation.errors)
        return errors

    def _rejected(self, reason: str) -> StepRunOutcome:
        return StepRunOutcome(awaiting_input=False, rejection_reason=reason)