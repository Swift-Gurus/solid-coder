"""
solid-description: Verifies that stop-evaluation respects session boundaries.
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
from harness.static_session_id_reader import StaticSessionIdReader

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


class TestFlowTransitionHandlerSessionIsolation(unittest.TestCase):
    """A Stop-hook gate scoped to one session must not see another session's pending run."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        (Path(self._tmpdir) / "runs").mkdir(parents=True)
        base_dir_resolver = RunsBaseDirResolver(project_dir_fn=lambda: Path(self._tmpdir))
        self.orchestrator_a = FlowRunOrchestratorFactory(
            base_dir_resolver=base_dir_resolver,
            plugin_root=Path(self._tmpdir),
            session_reader=StaticSessionIdReader("session-a"),
        ).build()
        self.evaluator_b = FlowStopEvaluator(
            FlowTransitionGateFactory(base_dir_resolver=base_dir_resolver, session_id="session-b").build()
        )

        self._flow_file = Path(self._tmpdir) / "two_step.yaml"
        self._flow_file.write_text(_TWO_STEP_FLOW_YAML)

    def test_session_b_gate_allows_stop_even_though_session_a_has_a_pending_run(self):
        self.orchestrator_a.flow_start(str(self._flow_file))  # session-a's run is left pending

        decision = self.evaluator_b.evaluate_stop({})

        self.assertTrue(decision.allow)


if __name__ == "__main__":
    unittest.main()
