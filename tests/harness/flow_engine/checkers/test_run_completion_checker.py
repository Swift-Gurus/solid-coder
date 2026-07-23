"""
solid-name: test_run_completion_checker
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests detecting done, timed-out, and still-in-progress run states.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, RunState, StepDef
from harness.run_completion_checker import RunCompletionChecker


class SpyEventAppender:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.events.append((path, event_type, payload))


class SpyActiveRunPointer:
    def __init__(self) -> None:
        self.deleted_for: list[Path] = []

    def read(self, base_dir: Path) -> str:
        raise NotImplementedError

    def write(self, base_dir: Path, run_id: str) -> None:
        raise NotImplementedError

    def delete(self, base_dir: Path) -> None:
        self.deleted_for.append(base_dir)


def _flow(max_turns: int = 10) -> FlowDef:
    return FlowDef(name="test_flow", max_turns=max_turns, steps=[StepDef(id="step-a", prompt="Do step-a")])


class TestRunCompletionChecker(unittest.TestCase):

    def test_returns_done_and_clears_active_run_when_all_steps_complete(self):
        appender = SpyEventAppender()
        active_run = SpyActiveRunPointer()
        sut = RunCompletionChecker(event_appender=appender, active_run=active_run)
        run_state = RunState(completed={"step-a": None}, running=[], turn_count=1, status="in_progress")

        result = sut.check(Path("/runs"), "run-1", "/run/events.jsonl", _flow(), run_state)

        self.assertEqual(result.status, "done")
        self.assertEqual(appender.events, [("/run/events.jsonl", "run_completed", {"run_id": "run-1"})])
        self.assertEqual(active_run.deleted_for, [Path("/runs")])

    def test_returns_timed_out_and_clears_active_run_when_max_turns_reached(self):
        appender = SpyEventAppender()
        active_run = SpyActiveRunPointer()
        sut = RunCompletionChecker(event_appender=appender, active_run=active_run)
        run_state = RunState(completed={}, running=[], turn_count=5, status="in_progress")

        result = sut.check(Path("/runs"), "run-1", "/run/events.jsonl", _flow(max_turns=5), run_state)

        self.assertEqual(result.status, "timed_out")
        self.assertEqual(appender.events, [("/run/events.jsonl", "run_timed_out", {"run_id": "run-1"})])
        self.assertEqual(active_run.deleted_for, [Path("/runs")])

    def test_returns_none_when_run_is_still_in_progress(self):
        appender = SpyEventAppender()
        active_run = SpyActiveRunPointer()
        sut = RunCompletionChecker(event_appender=appender, active_run=active_run)
        run_state = RunState(completed={}, running=[], turn_count=1, status="in_progress")

        result = sut.check(Path("/runs"), "run-1", "/run/events.jsonl", _flow(max_turns=10), run_state)

        self.assertIsNone(result)
        self.assertEqual(appender.events, [])
        self.assertEqual(active_run.deleted_for, [])

    def test_returns_failed_and_clears_active_run_when_a_step_exhausts_max_attempts(self):
        appender = SpyEventAppender()
        active_run = SpyActiveRunPointer()
        sut = RunCompletionChecker(event_appender=appender, active_run=active_run)
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[StepDef(id="step-a", prompt="p", max_attempts=3)])
        run_state = RunState(completed={}, running=[], turn_count=1, status="in_progress", attempts_used={"step-a": 3})

        result = sut.check(Path("/runs"), "run-1", "/run/events.jsonl", flow_def, run_state)

        self.assertEqual(result.status, "failed")
        self.assertEqual(appender.events, [("/run/events.jsonl", "run_failed", {"run_id": "run-1", "step_id": "step-a"})])
        self.assertEqual(active_run.deleted_for, [Path("/runs")])

    def test_ignores_attempts_used_for_an_already_completed_step(self):
        appender = SpyEventAppender()
        active_run = SpyActiveRunPointer()
        sut = RunCompletionChecker(event_appender=appender, active_run=active_run)
        flow_def = FlowDef(name="test_flow", max_turns=10, steps=[
            StepDef(id="step-a", prompt="p", max_attempts=3),
            StepDef(id="step-b", prompt="p"),
        ])
        run_state = RunState(
            completed={"step-a": None}, running=[], turn_count=1, status="in_progress",
            attempts_used={"step-a": 5},
        )

        result = sut.check(Path("/runs"), "run-1", "/run/events.jsonl", flow_def, run_state)

        self.assertIsNone(result)
        self.assertEqual(appender.events, [])


if __name__ == "__main__":
    unittest.main()
