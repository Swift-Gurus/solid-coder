"""
solid-name: test_process_step_handler
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-035]
solid-description: Tests delegation of process-step execution and submission validation.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_def import FlowDef
from harness.process_step_handler import ProcessStepHandler
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.step_run_outcome import StepRunOutcome
from harness.validation_result import ValidationResult


class StubExecutor:
    def __init__(self, outcome: StepRunOutcome) -> None:
        self.outcome = outcome
        self.step_instance = None
        self.step_def = None

    def run(self, step_instance, step_def):
        self.step_instance = step_instance
        self.step_def = step_def
        return self.outcome


class StubSubmissionValidator:
    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        self.step_instance = None
        self.outputs = None
        self.flow_def = None

    def validate(self, step_instance, outputs, flow_def):
        self.step_instance = step_instance
        self.outputs = outputs
        self.flow_def = flow_def
        return self.result


class TestProcessStepHandler(unittest.TestCase):
    def test_delegates_execution(self):
        expected = StepRunOutcome(awaiting_input=False, outputs={})
        executor = StubExecutor(expected)
        validator = StubSubmissionValidator(ValidationResult(ok=True))
        sut = ProcessStepHandler(executor, validator)
        instance = StepInstance(step_id="status", instance_id="status-1", item=None, prompt="")
        step = StepDef(id="status", prompt="", type="command", command="git status")

        outcome = sut.run(instance, step)

        self.assertIs(outcome, expected)
        self.assertIs(executor.step_instance, instance)
        self.assertIs(executor.step_def, step)

    def test_delegates_submission_validation(self):
        expected = ValidationResult(ok=True)
        executor = StubExecutor(StepRunOutcome(awaiting_input=False))
        validator = StubSubmissionValidator(expected)
        sut = ProcessStepHandler(executor, validator)
        instance = StepInstance(step_id="status", instance_id="status-1", item=None, prompt="")
        flow = FlowDef(name="flow", max_turns=10, steps=[])
        outputs = {"status": "ok"}

        result = sut.validate(instance, outputs, flow)

        self.assertIs(result, expected)
        self.assertIs(validator.step_instance, instance)
        self.assertIs(validator.outputs, outputs)
        self.assertIs(validator.flow_def, flow)


if __name__ == "__main__":
    unittest.main()
