"""
solid-description: Integration test proving flow_transition_gate blocks a real run left with a pending step.
solid-category: unit-test
"""

import io
import json
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from flow_transition_evaluating import build_default_flow_transition_gate  # noqa: E402
from flow_transition_gate import main  # noqa: E402
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402

_TWO_STEP_FLOW_YAML = textwrap.dedent("""\
    name: two_step
    max_turns: 10
    steps:
      - id: step_one
        prompt: Do step one
      - id: step_two
        prompt: Do step two
        depends_on: [step_one]
""")


class TestFlowTransitionGateIntegration(unittest.TestCase):
    """Drives a real FlowRunOrchestrator against real files on disk — no stubs, no live LLM."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        (Path(self._tmpdir) / "runs").mkdir(parents=True)
        base_dir_resolver = RunsBaseDirResolver(project_dir_fn=lambda: Path(self._tmpdir))
        self.orchestrator = FlowRunOrchestratorFactory(
            base_dir_resolver=base_dir_resolver, plugin_root=Path(self._tmpdir),
        ).build()
        self.gate = build_default_flow_transition_gate(base_dir_resolver=base_dir_resolver)

        self._flow_file = Path(self._tmpdir) / "two_step.yaml"
        self._flow_file.write_text(_TWO_STEP_FLOW_YAML)

    def _run_main(self) -> tuple:
        """Returns (exit_code, reason). exit_code is always 0 — the responder always
        exits(0); a block is distinguished by a {"decision": "block", "reason": ...}
        JSON payload on stdout, absent entirely on allow."""
        out = io.StringIO()
        exit_code = None
        with patch("sys.stdin", io.StringIO("{}")):
            with redirect_stdout(out):
                try:
                    main(gate=self.gate)
                except SystemExit as e:
                    exit_code = e.code
        stdout = out.getvalue()
        reason = json.loads(stdout)["reason"] if stdout else ""
        return exit_code, reason

    def test_allows_when_no_run_has_ever_started(self):
        exit_code, reason = self._run_main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(reason, "")

    def test_blocks_when_one_of_two_steps_submitted_and_the_other_left_pending(self):
        start_result = self.orchestrator.flow_start(str(self._flow_file))
        self.orchestrator.flow_next({s.instance_id: {} for s in start_result.steps})  # submits step_one only

        exit_code, reason = self._run_main()

        self.assertEqual(exit_code, 0)
        self.assertIn("step_two", reason)

    def test_allows_after_three_blocked_stop_attempts_exhaust_the_pending_step(self):
        self.orchestrator.flow_start(str(self._flow_file))  # step_one is pending, never submitted

        first = self._run_main()
        second = self._run_main()
        third = self._run_main()
        fourth = self._run_main()

        self.assertEqual(first[0], 0)
        self.assertIn("Call flow_next", first[1])
        self.assertEqual(second[0], 0)
        self.assertEqual(third[0], 0)
        self.assertIn("exhausted all 3 attempt", third[1])
        self.assertIn("step_one", third[1])
        # The run is now marked failed — status is no longer in_progress, so nothing to block.
        self.assertEqual(fourth[0], 0)
        self.assertEqual(fourth[1], "")

    def test_allows_once_every_step_is_submitted(self):
        start_result = self.orchestrator.flow_start(str(self._flow_file))
        next1 = self.orchestrator.flow_next({s.instance_id: {} for s in start_result.steps})
        final = self.orchestrator.flow_next({s.instance_id: {} for s in next1.steps})
        self.assertEqual(final.status, "done")

        exit_code, reason = self._run_main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
