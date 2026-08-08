"""
solid-name: test_step_output_validator
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests validating step outputs against declared specs, including malformed (non-object) outputs.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, OutputSpec, StepDef, StepInstance
from harness.step_output_validator import StepOutputValidator


class StubSchemaValidator:
    def __init__(self, errors: list[str] | None = None) -> None:
        self._errors = errors or []

    def validate(self, output_spec: OutputSpec, value) -> "_Result":
        return _Result(ok=not self._errors, errors=self._errors)


class _Result:
    def __init__(self, ok: bool, errors: list[str]) -> None:
        self.ok = ok
        self.errors = errors


def _flow_with_output(name: str, output_name: str) -> FlowDef:
    return FlowDef(name="test_flow", max_turns=10, steps=[
        StepDef(id=name, prompt="Do it", outputs=[OutputSpec(name=output_name, type="data", schema={"type": "string"})]),
    ])


def _instance(step_id: str) -> StepInstance:
    return StepInstance(step_id=step_id, instance_id=f"{step_id}-1", item=None, prompt="Do it")


class TestStepOutputValidator(unittest.TestCase):

    def test_valid_object_outputs_pass_when_schema_ok(self):
        sut = StepOutputValidator(schema_validator=StubSchemaValidator())
        flow_def = _flow_with_output("greet", "greeting")

        errors = sut.validate([_instance("greet")], {"greet-1": {"greeting": "hi"}}, flow_def)

        self.assertEqual(errors, [])

    def test_schema_violation_is_reported(self):
        sut = StepOutputValidator(schema_validator=StubSchemaValidator(errors=["not a string"]))
        flow_def = _flow_with_output("greet", "greeting")

        errors = sut.validate([_instance("greet")], {"greet-1": {"greeting": 123}}, flow_def)

        self.assertEqual(errors, ["not a string"])

    def test_non_object_instance_outputs_reports_clean_shape_error_without_crashing(self):
        sut = StepOutputValidator(schema_validator=StubSchemaValidator())
        flow_def = _flow_with_output("greet", "greeting")

        errors = sut.validate([_instance("greet")], {"greet-1": "just a string"}, flow_def)

        self.assertEqual(len(errors), 1)
        self.assertIn("greet-1", errors[0])
        self.assertIn("must be an object", errors[0])

    def test_missing_instance_id_defaults_to_empty_object(self):
        sut = StepOutputValidator(schema_validator=StubSchemaValidator())
        flow_def = _flow_with_output("greet", "greeting")

        errors = sut.validate([_instance("greet")], {}, flow_def)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
