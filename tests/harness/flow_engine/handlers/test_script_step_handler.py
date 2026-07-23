"""
solid-name: test_script_step_handler
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests that script steps auto-execute their declared command and delegate outcome evaluation, with a trivial pass-through validate.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, StepDef, StepInstance
from harness.script_execution_result import ScriptExecutionResult
from harness.script_step_handler import ScriptStepHandler
from harness.step_run_outcome import StepRunOutcome


class StubRunner:
    def __init__(self, result: ScriptExecutionResult) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def run(self, command, timeout_seconds):
        self.calls.append((command, timeout_seconds))
        return self._result


class StubEvaluator:
    def __init__(self, outcome: StepRunOutcome) -> None:
        self._outcome = outcome
        self.calls: list[tuple] = []

    def evaluate(self, result, step):
        self.calls.append((result, step))
        return self._outcome


class TestScriptStepHandler(unittest.TestCase):

    def test_run_executes_command_and_delegates_to_evaluator(self):
        step = StepDef(id="a", prompt="", type="script", command=["run.sh"], timeout_seconds=30)
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="")
        script_result = ScriptExecutionResult(exit_code=0, stdout="{}", stderr="", timed_out=False)
        runner = StubRunner(script_result)
        expected_outcome = StepRunOutcome(awaiting_input=False, outputs={})
        evaluator = StubEvaluator(expected_outcome)
        sut = ScriptStepHandler(runner=runner, evaluator=evaluator)

        outcome = sut.run(instance, step)

        self.assertIs(outcome, expected_outcome)
        self.assertEqual(runner.calls, [(["run.sh"], 30)])
        self.assertEqual(evaluator.calls, [(script_result, step)])

    def test_validate_is_a_trivial_pass_through(self):
        sut = ScriptStepHandler(runner=StubRunner(None), evaluator=StubEvaluator(None))
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="")

        result = sut.validate(instance, {"anything": True}, FlowDef(name="f", max_turns=10, steps=[]))

        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
