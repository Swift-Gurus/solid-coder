"""Tests continuing an isolated workflow from a different model session."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import (  # noqa: E402
    FlowRunOrchestratorFactory,
)
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402


"""
solid-name: TestIsolatedRunSessionHandoff
solid-category: integration-test
solid-spec: [SPEC-031]
solid-description: Proves a child model session can continue and inspect an isolated run created by its parent session.
"""
class TestIsolatedRunSessionHandoff(unittest.TestCase):
    def test_child_session_completes_parent_isolated_run_by_explicit_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            workflow = project_root / "workflow.yaml"
            workflow.write_text(
                textwrap.dedent(
                    """
                    name: Session handoff
                    max_turns: 2
                    steps:
                      - id: inspect
                        prompt: Inspect the supplied source.
                        outputs:
                          - name: result
                            type: data
                            schema: {type: string}
                    """
                ).lstrip()
            )
            parent = self._orchestrator(project_root, "parent-session")
            child = self._orchestrator(project_root, "child-session")

            started = parent.flow_start(str(workflow), isolated=True)
            run_directory = project_root / "subagents" / started.run_id
            self.assertEqual(list(run_directory.glob("active*.json")), [])

            completed = child.flow_next(
                {started.steps[0].instance_id: {"result": "reviewed"}},
                run_id=started.run_id,
            )
            status = parent.flow_status(started.run_id)

            self.assertIsNone(completed.error, completed.error)
            self.assertEqual(completed.status, "done", repr(completed))
            self.assertEqual(status.status, "done")
            self.assertIsNone(status.error)
            self.assertFalse((run_directory / started.run_id).exists())
            self.assertEqual(list(run_directory.glob("active*.json")), [])

    def _orchestrator(self, project_root: Path, session_id: str):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: project_root,
            ),
            plugin_root=project_root,
            project_directory=lambda: project_root,
            session_reader=StaticSessionIdReader(session_id),
        ).build()


if __name__ == "__main__":
    unittest.main()
