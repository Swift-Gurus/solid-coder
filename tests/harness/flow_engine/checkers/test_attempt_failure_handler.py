"""
solid-name: test_attempt_failure_handler
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests recording a failed attempt as an event, optionally reopening the step, and delegating to run-completion checking to detect attempts exhaustion.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doubles import SpyCompletionChecker, SpyEventAppender
from harness.attempt_failure_handler import AttemptFailureHandler
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState


class StubEventReplayer:
    def __init__(self, run_state: RunState) -> None:
        self._run_state = run_state

    def replay(self, path: str) -> RunState:
        return self._run_state


class TestAttemptFailureHandler(unittest.TestCase):

    def test_appends_step_attempt_failed_event_when_not_reopening(self):
        appender = SpyEventAppender()
        sut = AttemptFailureHandler(
            event_appender=appender,
            event_replayer=StubEventReplayer(RunState(completed={}, running=[], turn_count=0, status="in_progress")),
            completion_checker=SpyCompletionChecker(None),
        )

        sut.handle("gate", "bad shape", reopen=False, base_dir=Path("/runs"), run_id="r1",
                   events_path="events.jsonl", flow_def=FlowDef(name="f", max_turns=10, steps=[]))

        self.assertEqual(appender.events, [("events.jsonl", "step_attempt_failed", {"step_id": "gate", "reason": "bad shape"})])

    def test_appends_step_rejected_event_when_reopening(self):
        appender = SpyEventAppender()
        sut = AttemptFailureHandler(
            event_appender=appender,
            event_replayer=StubEventReplayer(RunState(completed={}, running=[], turn_count=0, status="in_progress")),
            completion_checker=SpyCompletionChecker(None),
        )

        sut.handle("writer", "rejected", reopen=True, base_dir=Path("/runs"), run_id="r1",
                   events_path="events.jsonl", flow_def=FlowDef(name="f", max_turns=10, steps=[]))

        self.assertEqual(appender.events, [("events.jsonl", "step_rejected", {"step_id": "writer", "reason": "rejected"})])

    def test_returns_terminal_result_when_completion_checker_reports_failed(self):
        terminal = FlowNextResult(status="failed")
        checker = SpyCompletionChecker(terminal)
        sut = AttemptFailureHandler(
            event_appender=SpyEventAppender(),
            event_replayer=StubEventReplayer(RunState(completed={}, running=[], turn_count=0, status="in_progress")),
            completion_checker=checker,
        )

        result = sut.handle("gate", "boom", reopen=False, base_dir=Path("/runs"), run_id="r1",
                             events_path="events.jsonl", flow_def=FlowDef(name="f", max_turns=10, steps=[]))

        self.assertIs(result, terminal)

    def test_returns_none_when_attempts_remain(self):
        checker = SpyCompletionChecker(None)
        sut = AttemptFailureHandler(
            event_appender=SpyEventAppender(),
            event_replayer=StubEventReplayer(RunState(completed={}, running=[], turn_count=0, status="in_progress")),
            completion_checker=checker,
        )

        result = sut.handle("gate", "boom", reopen=False, base_dir=Path("/runs"), run_id="r1",
                             events_path="events.jsonl", flow_def=FlowDef(name="f", max_turns=10, steps=[]))

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
