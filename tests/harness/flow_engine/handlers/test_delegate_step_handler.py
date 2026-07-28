"""
solid-name: test_delegate_step_handler
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests routing delegate steps by mode to an agent-awaited subagent instruction or a server-driven session, and delegating validation.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.delegate_instruction_builder import build_delegate_instruction
from harness.delegate_step_handler import DelegateStepHandler
from harness.models import FlowDef, StepDef, StepInstance, ValidationResult
from harness.step_run_outcome import StepRunOutcome


class StubAgentHandler:
    def __init__(self, run_outcome=None, validate_result=None) -> None:
        self._run_outcome = run_outcome or StepRunOutcome(awaiting_input=True)
        self._validate_result = validate_result or ValidationResult(ok=True)
        self.run_calls: list[tuple] = []
        self.validate_calls: list[tuple] = []

    def run(self, step_instance, step_def) -> StepRunOutcome:
        self.run_calls.append((step_instance, step_def))
        return self._run_outcome

    def validate(self, step_instance, outputs, flow_def) -> ValidationResult:
        self.validate_calls.append((step_instance, outputs, flow_def))
        return self._validate_result


class StubSessionRunner:
    def __init__(self, outcome: StepRunOutcome) -> None:
        self._outcome = outcome
        self.calls: list[str] = []

    def run(self, prompt: str) -> StepRunOutcome:
        self.calls.append(prompt)
        return self._outcome


class TestDelegateStepHandler(unittest.TestCase):

    def test_subagent_mode_delegates_run_to_agent_handler(self):
        agent_handler = StubAgentHandler()
        sut = DelegateStepHandler(agent_handler=agent_handler, session_runner=StubSessionRunner(None))
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        step_def = StepDef(id="a", prompt="p", type="delegate", mode="subagent")

        outcome = sut.run(instance, step_def)

        self.assertTrue(outcome.awaiting_input)
        self.assertEqual(agent_handler.run_calls, [(instance, step_def)])

    def test_session_mode_delegates_run_to_session_runner_with_the_isolation_instruction(self):
        expected_outcome = StepRunOutcome(awaiting_input=False, outputs={})
        session_runner = StubSessionRunner(expected_outcome)
        sut = DelegateStepHandler(agent_handler=StubAgentHandler(), session_runner=session_runner)
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="Call flow_start with flow=\"x\".")
        step_def = StepDef(id="a", prompt="p", type="delegate", mode="session")

        outcome = sut.run(instance, step_def)

        self.assertIs(outcome, expected_outcome)
        self.assertEqual(session_runner.calls, [build_delegate_instruction(instance.prompt)])

    def test_session_mode_does_not_call_agent_handler(self):
        agent_handler = StubAgentHandler()
        sut = DelegateStepHandler(
            agent_handler=agent_handler,
            session_runner=StubSessionRunner(StepRunOutcome(awaiting_input=False, outputs={})),
        )
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        step_def = StepDef(id="a", prompt="p", type="delegate", mode="session")

        sut.run(instance, step_def)

        self.assertEqual(agent_handler.run_calls, [])

    def test_validate_always_delegates_to_agent_handler(self):
        agent_handler = StubAgentHandler(validate_result=ValidationResult(ok=False, errors=["bad"]))
        sut = DelegateStepHandler(agent_handler=agent_handler, session_runner=StubSessionRunner(None))
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        flow_def = FlowDef(name="f", max_turns=10, steps=[])

        result = sut.validate(instance, {"x": 1}, flow_def)

        self.assertFalse(result.ok)
        self.assertEqual(agent_handler.validate_calls, [(instance, {"x": 1}, flow_def)])


if __name__ == "__main__":
    unittest.main()
