"""
solid-name: test_workflow_catalog_process_integration
solid-category: integration-test
solid-spec: [SPEC-035]
solid-description: Verifies nested workflow packages execute process steps internally and expose only agent steps.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver

_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "workflow_catalog_e2e"
_MODEL_SESSION_ID = "model-session"


class _AllowlistResolver:
    def resolve(self) -> list[str]:
        return ["python3", "bash"]


class _SessionReader:
    def read_session_id(self) -> str:
        return _MODEL_SESSION_ID


class TestWorkflowCatalogProcessIntegration(unittest.TestCase):
    def setUp(self):
        self._temporary_project = tempfile.TemporaryDirectory(
            prefix="solid-coder-catalog-process-"
        )
        self.project_root = Path(self._temporary_project.name)
        shutil.copytree(
            _FIXTURE_ROOT / "workflows",
            self.project_root / ".solid-coder" / "workflows",
        )
        self.runs_dir = self.project_root / "runs"
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
            command_allowlist_resolver=_AllowlistResolver(),
            session_reader=_SessionReader(),
        ).build()

    def tearDown(self):
        self._temporary_project.cleanup()

    def test_nested_process_steps_are_engine_owned_and_only_agents_are_returned(self):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.project_root)}):
            started = self.sut.flow_start("e2e-catalog-combined")

            self.assertEqual(
                [step.step_id for step in started.steps],
                ["first.verify_existing", "second.verify_existing"],
            )
            after_shared_agents = self.sut.flow_next(
                {
                    step.instance_id: {"existing": True}
                    for step in started.steps
                }
            )
            self.assertEqual(
                [step.step_id for step in after_shared_agents.steps],
                ["confirm_combined"],
            )
            completed = self.sut.flow_next(
                {
                    after_shared_agents.steps[0].instance_id: {"combined": True}
                }
            )

        self.assertEqual(completed.status, "done", completed.error)
        events = self._events(started.run_id)
        self.assertEqual(
            self._completed_steps(events),
            [
                "first.process.structured_script",
                "first.process.inline_command",
                "second.process.structured_script",
                "second.process.inline_command",
                "first.verify_existing",
                "second.verify_existing",
                "confirm_combined",
            ],
        )
        self.assertEqual(
            self._completed_steps_for_session(events, "engine"),
            [
                "first.process.structured_script",
                "first.process.inline_command",
                "second.process.structured_script",
                "second.process.inline_command",
            ],
        )
        self.assertEqual(
            self._completed_steps_for_session(events, _MODEL_SESSION_ID),
            ["first.verify_existing", "second.verify_existing", "confirm_combined"],
        )
        self.assertTrue(
            self._step_output(
                events,
                "first.process.structured_script",
                "script_ready",
            )
        )
        self.assertTrue(
            self._step_output(
                events,
                "second.process.inline_command",
                "command_ready",
            )
        )

    def _events(self, run_id: str) -> list[dict]:
        events_path = self.runs_dir / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _completed_steps(self, events: list[dict]) -> list[str]:
        return [
            event["step_id"]
            for event in events
            if event.get("event") == "step_completed"
        ]

    def _completed_steps_for_session(
        self,
        events: list[dict],
        session_id: str,
    ) -> list[str]:
        return [
            event["step_id"]
            for event in events
            if event.get("event") == "step_completed"
            and event.get("session_id") == session_id
        ]

    def _step_output(
        self,
        events: list[dict],
        step_id: str,
        output_name: str,
    ) -> object:
        event = next(
            item
            for item in events
            if item.get("event") == "step_completed"
            and item.get("step_id") == step_id
        )
        return event["outputs"][output_name]


if __name__ == "__main__":
    unittest.main()
