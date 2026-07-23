"""
solid-name: test_script_outcome_evaluator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests evaluating a script step's execution result into recorded outputs or a rejection reason.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import OutputSpec, StepDef, ValidationResult
from harness.schema_validator import SchemaValidator
from harness.script_execution_result import ScriptExecutionResult
from harness.script_outcome_evaluator import ScriptOutcomeEvaluator


class StubDataValidator:
    def __init__(self, result: ValidationResult) -> None:
        self._result = result

    def validate(self, output_spec, value) -> ValidationResult:
        return self._result


def _step(outputs=None) -> StepDef:
    return StepDef(id="gate", prompt="", type="script", command=["run.sh"], outputs=outputs or [])


class TestScriptOutcomeEvaluator(unittest.TestCase):

    def _sut(self, ok=True, errors=None) -> ScriptOutcomeEvaluator:
        validator = SchemaValidator(validators={"data": StubDataValidator(ValidationResult(ok=ok, errors=errors or []))})
        return ScriptOutcomeEvaluator(schema_validator=validator)

    def test_records_outputs_on_zero_exit_and_valid_schema(self):
        step = _step(outputs=[OutputSpec(name="result", type="data")])
        result = ScriptExecutionResult(exit_code=0, stdout='{"result": "ok"}', stderr="", timed_out=False)

        outcome = self._sut(ok=True).evaluate(result, step)

        self.assertFalse(outcome.awaiting_input)
        self.assertEqual(outcome.outputs, {"result": "ok"})
        self.assertIsNone(outcome.rejection_reason)

    def test_rejects_on_non_zero_exit_with_stderr_as_reason(self):
        step = _step()
        result = ScriptExecutionResult(exit_code=1, stdout="", stderr="boom", timed_out=False)

        outcome = self._sut().evaluate(result, step)

        self.assertIsNone(outcome.outputs)
        self.assertEqual(outcome.rejection_reason, "boom")

    def test_rejects_on_timeout(self):
        step = _step()
        result = ScriptExecutionResult(exit_code=None, stdout="", stderr="", timed_out=True)

        outcome = self._sut().evaluate(result, step)

        self.assertIsNone(outcome.outputs)
        self.assertIsNotNone(outcome.rejection_reason)

    def test_rejects_on_invalid_json_stdout(self):
        step = _step()
        result = ScriptExecutionResult(exit_code=0, stdout="not json", stderr="", timed_out=False)

        outcome = self._sut().evaluate(result, step)

        self.assertIsNone(outcome.outputs)
        self.assertIsNotNone(outcome.rejection_reason)

    def test_rejects_on_schema_violation(self):
        step = _step(outputs=[OutputSpec(name="result", type="data")])
        result = ScriptExecutionResult(exit_code=0, stdout='{"result": "bad"}', stderr="", timed_out=False)

        outcome = self._sut(ok=False, errors=["schema mismatch"]).evaluate(result, step)

        self.assertIsNone(outcome.outputs)
        self.assertIn("schema mismatch", outcome.rejection_reason)


if __name__ == "__main__":
    unittest.main()
