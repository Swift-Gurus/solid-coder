"""
solid-description: Validates flow stop decisions based on step completion state.
solid-category: unit-test
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))

from flow_transition_gate_factory import FlowTransitionGateFactory
from flow_transition_handler import FlowStopEvaluator
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver

_TWO_STEP_FLOW_YAML = textwrap.dedent("""
    name: two_step
    max_turns: 10
    steps:
      - id: step_one
        prompt: Do step one
      - id: step_two
        prompt: Do step two
        depends_on: [step_one]
""")


class TestFlowTransitionHandlerIntegration(unittest.TestCase):
    """Drives a real FlowRunOrchestrator against real files on disk — no stubs, no live LLM."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        (Path(self._tmpdir) / "runs").mkdir(parents=True)
        base_dir_resolver = RunsBaseDirResolver(project_dir_fn=lambda: Path(self._tmpdir))
        self.orchestrator = FlowRunOrchestratorFactory(
            base_dir_resolver=base_dir_resolver, plugin_root=Path(self._tmpdir),
        ).build()
        gate = FlowTransitionGateFactory(base_dir_resolver=base_dir_resolver).build()
        self.evaluator = FlowStopEvaluator(gate)

        self._flow_file = Path(self._tmpdir) / "two_step.yaml"
        self._flow_file.write_text(_TWO_STEP_FLOW_YAML)

    def _evaluate(self) -> tuple:
        decision = self.evaluator.evaluate_stop({})
        return decision.allow, decision.reason or ""

    def test_allows_when_no_run_has_ever_started(self):
        allow, reason = self._evaluate()

        self.assertTrue(allow)
        self.assertEqual(reason, "")

    def test_blocks_when_one_of_two_steps_submitted_and_the_other_left_pending(self):
        start_result = self.orchestrator.flow_start(str(self._flow_file))
        self.orchestrator.flow_next({s.instance_id: {} for s in start_result.steps})  # submits step_one only

        allow, reason = self._evaluate()

        self.assertFalse(allow)
        self.assertIn("step_two", reason)

    def test_allows_after_three_blocked_stop_attempts_exhaust_the_pending_step(self):
        self.orchestrator.flow_start(str(self._flow_file))  # step_one is pending, never submitted

        first = self._evaluate()
        second = self._evaluate()
        third = self._evaluate()
        fourth = self._evaluate()

        self.assertFalse(first[0])
        self.assertIn("Call flow_next", first[1])
        self.assertFalse(second[0])
        self.assertFalse(third[0])
        self.assertIn("exhausted all 3 attempt", third[1])
        self.assertIn("step_one", third[1])
        # The run is now marked failed — status is no longer in_progress, so nothing to block.
        self.assertTrue(fourth[0])
        self.assertEqual(fourth[1], "")

    def test_allows_once_every_step_is_submitted(self):
        start_result = self.orchestrator.flow_start(str(self._flow_file))
        next1 = self.orchestrator.flow_next({s.instance_id: {} for s in start_result.steps})
        final = self.orchestrator.flow_next({s.instance_id: {} for s in next1.steps})
        self.assertEqual(final.status, "done")

        allow, reason = self._evaluate()

        self.assertTrue(allow)
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
