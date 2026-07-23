"""
solid-name: test_output_submission_advancer
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests per-instance output validation via declared-type handlers, attempt-failure routing for invalid submissions, and recording plus turn advancement for valid ones.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState, StepDef, StepInstance, ValidationResult
from harness.output_submission_advancer import OutputSubmissionAdvancer


class ScriptedHandlerResolver:
    def __init__(self, results: dict[str, ValidationResult]) -> None:
        self._results = results

    def resolve(self, step_type: str):
        return self

    def validate(self, instance, outputs, flow_def):
        return self._results[instance.instance_id]


class SpyAttemptFailureHandler:
    def __init__(self, result=None) -> None:
        self._result = result
        self.calls: list[dict] = []

    def handle(self, **kwargs):
        self.calls.append(kwargs)
        return self._result


class StubSessionReader:
    def read_session_id(self) -> str:
        return "session-1"


class SpyOutputRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def record(self, events_path, ready, step_outputs, session_id) -> None:
        self.calls.append((events_path, ready, step_outputs, session_id))


class SpyTurnAdvancer:
    def __init__(self, run_state: RunState) -> None:
        self._run_state = run_state
        self.calls: list[str] = []

    def advance(self, events_path: str) -> RunState:
        self.calls.append(events_path)
        return self._run_state


def _flow_def() -> FlowDef:
    return FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p")])


class OutputSubmissionAdvancerFactory:
    """Builds an OutputSubmissionAdvancer with sensible stub/spy defaults; tests override only what they vary."""

    def __init__(self) -> None:
        self.step_handler_resolver = ScriptedHandlerResolver({})
        self.attempt_failure_handler = SpyAttemptFailureHandler()
        self.session_reader = StubSessionReader()
        self.output_recorder = SpyOutputRecorder()
        self.turn_advancer = SpyTurnAdvancer(RunState(completed={}, running=[], turn_count=0, status="in_progress"))

    def with_step_handler_resolver(self, resolver) -> "OutputSubmissionAdvancerFactory":
        self.step_handler_resolver = resolver
        return self

    def with_attempt_failure_handler(self, handler) -> "OutputSubmissionAdvancerFactory":
        self.attempt_failure_handler = handler
        return self

    def with_turn_advancer(self, advancer) -> "OutputSubmissionAdvancerFactory":
        self.turn_advancer = advancer
        return self

    def make_sut(self) -> OutputSubmissionAdvancer:
        return OutputSubmissionAdvancer(
            step_handler_resolver=self.step_handler_resolver,
            attempt_failure_handler=self.attempt_failure_handler,
            session_reader=self.session_reader,
            output_recorder=self.output_recorder,
            turn_advancer=self.turn_advancer,
        )


class TestOutputSubmissionAdvancer(unittest.TestCase):

    def test_records_and_advances_when_all_submitted_outputs_are_valid(self):
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(completed={}, running=[], turn_count=1, status="in_progress")
        factory = OutputSubmissionAdvancerFactory().with_step_handler_resolver(
            ScriptedHandlerResolver({"a-1": ValidationResult(ok=True)})
        ).with_turn_advancer(SpyTurnAdvancer(run_state))

        outcome = factory.make_sut().submit("events.jsonl", Path("/runs"), "run-1", [instance], {"a-1": {"x": 1}}, _flow_def())

        self.assertIs(outcome.run_state, run_state)
        self.assertIsNone(outcome.terminal)
        self.assertEqual(factory.output_recorder.calls, [("events.jsonl", [instance], {"a-1": {"x": 1}}, "session-1")])
        self.assertEqual(factory.turn_advancer.calls, ["events.jsonl"])

    def test_routes_invalid_submission_through_attempt_failure_handler_without_recording(self):
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        failure_handler = SpyAttemptFailureHandler(result=None)
        factory = OutputSubmissionAdvancerFactory().with_step_handler_resolver(
            ScriptedHandlerResolver({"a-1": ValidationResult(ok=False, errors=["bad shape"])})
        ).with_attempt_failure_handler(failure_handler)

        outcome = factory.make_sut().submit("events.jsonl", Path("/runs"), "run-1", [instance], {"a-1": {}}, _flow_def())

        self.assertIsNone(outcome.run_state)
        self.assertIsNone(outcome.terminal)
        self.assertEqual(factory.output_recorder.calls, [])
        self.assertEqual(failure_handler.calls[0]["step_id"], "a")
        self.assertEqual(failure_handler.calls[0]["reason"], "bad shape")
        self.assertFalse(failure_handler.calls[0]["reopen"])

    def test_returns_terminal_when_attempt_failure_handler_reports_exhaustion(self):
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        terminal = FlowNextResult(status="failed")
        factory = OutputSubmissionAdvancerFactory().with_step_handler_resolver(
            ScriptedHandlerResolver({"a-1": ValidationResult(ok=False, errors=["bad"])})
        ).with_attempt_failure_handler(SpyAttemptFailureHandler(result=terminal))

        outcome = factory.make_sut().submit("events.jsonl", Path("/runs"), "run-1", [instance], {"a-1": {}}, _flow_def())

        self.assertIs(outcome.terminal, terminal)

    def test_ignores_ready_instances_with_no_submitted_output(self):
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        factory = OutputSubmissionAdvancerFactory()

        outcome = factory.make_sut().submit("events.jsonl", Path("/runs"), "run-1", [instance], {}, _flow_def())

        self.assertIsNone(outcome.run_state)
        self.assertEqual(factory.output_recorder.calls, [])


if __name__ == "__main__":
    unittest.main()
