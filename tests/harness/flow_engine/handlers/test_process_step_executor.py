"""
solid-name: test_process_step_executor
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Tests typed process resolution, execution, and outcome evaluation for workflow steps.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.inline_command_execution import InlineCommandExecution
from harness.process_step_executor import ProcessStepExecutor
from harness.script_execution_result import ScriptExecutionResult
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.step_run_outcome import StepRunOutcome


class StubExecutionResolver:
    def __init__(self, execution) -> None:
        self.execution = execution
        self.step = None

    def resolve(self, step):
        self.step = step
        return self.execution


class StubRunner:
    def __init__(self, result: ScriptExecutionResult) -> None:
        self.result = result
        self.execution = None
        self.timeout_seconds = None

    def run(self, execution, timeout_seconds):
        self.execution = execution
        self.timeout_seconds = timeout_seconds
        return self.result


class StubEvaluator:
    def __init__(self, outcome: StepRunOutcome) -> None:
        self.outcome = outcome
        self.result = None
        self.step = None

    def evaluate(self, result, step):
        self.result = result
        self.step = step
        return self.outcome


class TestProcessStepExecutor(unittest.TestCase):
    def test_runs_resolved_execution_and_evaluates_result(self):
        execution = InlineCommandExecution("bash", "git status")
        process_result = ScriptExecutionResult(0, "clean", "", False)
        expected = StepRunOutcome(awaiting_input=False, outputs={})
        resolver = StubExecutionResolver(execution)
        runner = StubRunner(process_result)
        evaluator = StubEvaluator(expected)
        sut = ProcessStepExecutor(resolver, runner, evaluator)
        instance = StepInstance(step_id="status", instance_id="status-1", item=None, prompt="")
        step = StepDef(
            id="status",
            prompt="",
            type="command",
            command="git status",
            timeout_seconds=30,
        )

        outcome = sut.run(instance, step)

        self.assertIs(outcome, expected)
        self.assertIs(resolver.step, step)
        self.assertIs(runner.execution, execution)
        self.assertEqual(runner.timeout_seconds, 30)
        self.assertIs(evaluator.result, process_result)
        self.assertIs(evaluator.step, step)


if __name__ == "__main__":
    unittest.main()
