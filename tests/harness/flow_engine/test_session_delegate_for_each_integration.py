"""Validates MCP-owned session delegate fan-out and deterministic fan-in."""

from __future__ import annotations

import sys
import json
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator import FlowRunOrchestrator  # noqa: E402
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.step_run_outcome import StepRunOutcome  # noqa: E402


_FLOW = """
    name: session_delegate_for_each
    max_turns: 20
    steps:
      - id: prepare
        prompt: Prepare review targets.
        outputs:
          - name: units
            type: data
            schema:
              type: array
              items:
                type: string

      - id: review
        type: delegate
        mode: session
        prompt: Review {{item}}.
        depends_on: [prepare]
        for_each: "{{steps.prepare.outputs.units}}"
        max_attempts: 2
        outputs:
          - name: finding
            type: data
            schema:
              type: string

      - id: summarize
        prompt: Summarize {{steps.review.outputs.finding}}.
        depends_on: [review]
"""


class ControlledSessionRunner:
    def __init__(
        self,
        barrier: threading.Barrier | None = None,
        invalid_first_units: set[str] | None = None,
    ) -> None:
        self._barrier = barrier
        self._invalid_first_units = invalid_first_units or set()
        self._lock = threading.Lock()
        self.calls: list[str] = []
        self.prompts: list[str] = []
        self.call_counts: dict[str, int] = {}

    def run(self, prompt: str) -> StepRunOutcome:
        unit = self._unit_in(prompt)
        with self._lock:
            self.calls.append(unit)
            self.prompts.append(prompt)
            self.call_counts[unit] = self.call_counts.get(unit, 0) + 1
            attempt = self.call_counts[unit]
        if self._barrier is not None:
            self._barrier.wait(timeout=2)
        time.sleep({"Alpha": 0.03, "Beta": 0.02, "Gamma": 0.01}[unit])
        if unit in self._invalid_first_units and attempt == 1:
            return StepRunOutcome(awaiting_input=False, outputs={"finding": 1})
        return StepRunOutcome(
            awaiting_input=False,
            outputs={"finding": f"{unit} finding"},
        )

    def _unit_in(self, prompt: str) -> str:
        return next(
            unit for unit in ["Alpha", "Beta", "Gamma"] if unit in prompt
        )


class TestSessionDelegateForEachIntegration(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.project_root = Path(temporary_directory.name)
        self.flow_path = self.project_root / "session-delegate.yaml"
        self.flow_path.write_text(textwrap.dedent(_FLOW), encoding="utf-8")

    def test_sessions_overlap_and_fan_in_outputs_in_source_order(self) -> None:
        runner = ControlledSessionRunner(barrier=threading.Barrier(3))
        sut = self._make_orchestrator(runner)

        result = self._start_fan_out(sut, ["Alpha", "Beta", "Gamma"])

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        prompt = result.steps[0].prompt
        self.assertLess(
            prompt.index("Alpha finding"),
            prompt.index("Beta finding"),
        )
        self.assertLess(
            prompt.index("Beta finding"),
            prompt.index("Gamma finding"),
        )
        self.assertEqual(runner.call_counts, {"Alpha": 1, "Beta": 1, "Gamma": 1})
        self.assertTrue(
            all("isolated=true" in prompt for prompt in runner.prompts)
        )

    def test_invalid_instance_retries_without_relaunching_valid_siblings(self) -> None:
        runner = ControlledSessionRunner(invalid_first_units={"Alpha"})
        sut = self._make_orchestrator(runner)

        result = self._start_fan_out(sut, ["Alpha", "Beta", "Gamma"])

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertEqual(runner.call_counts, {"Alpha": 2, "Beta": 1, "Gamma": 1})

    def test_records_each_invalid_sibling_attempt_before_retrying_batch(self) -> None:
        runner = ControlledSessionRunner(
            invalid_first_units={"Alpha", "Beta"}
        )
        sut = self._make_orchestrator(runner)

        result = self._start_fan_out(sut, ["Alpha", "Beta", "Gamma"])

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        events_path = next((self.project_root / "runs").glob("*/events.jsonl"))
        failed_attempt_ids = [
            event["attempt_id"]
            for event in (
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
            )
            if event["event"] == "step_attempt_failed"
        ]
        self.assertEqual(failed_attempt_ids, ["review-1", "review-2"])
        self.assertEqual(runner.call_counts, {"Alpha": 2, "Beta": 2, "Gamma": 1})

    def test_empty_collection_starts_no_sessions(self) -> None:
        runner = ControlledSessionRunner()
        sut = self._make_orchestrator(runner)

        result = self._start_fan_out(sut, [])

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertEqual(runner.calls, [])

    def test_replay_does_not_relaunch_completed_sessions(self) -> None:
        runner = ControlledSessionRunner()
        first = self._make_orchestrator(runner)
        first_result = self._start_fan_out(first, ["Alpha", "Beta", "Gamma"])
        self.assertEqual([step.step_id for step in first_result.steps], ["summarize"])

        replay_runner = ControlledSessionRunner()
        replayed = self._make_orchestrator(replay_runner).flow_next()

        self.assertEqual([step.step_id for step in replayed.steps], ["summarize"])
        self.assertEqual(replay_runner.calls, [])

    def _make_orchestrator(
        self,
        runner: ControlledSessionRunner,
    ) -> FlowRunOrchestrator:
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
            session_delegate_runner=runner,
            session_delegate_max_workers=3,
        ).build()

    def _start_fan_out(
        self,
        sut: FlowRunOrchestrator,
        units: list[str],
    ):
        started = sut.flow_start(str(self.flow_path))
        return sut.flow_next(
            {started.steps[0].instance_id: {"units": units}}
        )


if __name__ == "__main__":
    unittest.main()
