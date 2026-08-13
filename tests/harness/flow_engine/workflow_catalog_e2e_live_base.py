"""Defines the backend-neutral live workflow-catalog contract."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

_HARNESS_DIR = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
_MCP_HEALTH_CONFIG = _MCP_SERVER / "health" / "config"
for _directory in (_HARNESS_DIR, _MCP_SERVER, _MCP_HEALTH_CONFIG):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness_factory import HookUtilsTomlLoader  # noqa: E402
from hook_utils import solid_coder_project_dir  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_running import LiveSessionRunning  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402
from model_profile_environment import model_profile_environment  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402

_PLUGIN_ROOT = _MCP_SERVER.parent
_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "workflow_catalog_e2e"
_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_status,flow_start,flow_next,flow_status"
)
_FAILED_EVENTS = {"step_attempt_failed", "step_rejected", "run_failed"}


"""
solid-name: WorkflowCatalogE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-035]
solid-description: Verifies bare-ID package discovery and nested workflow-ID composition through any live model backend.
"""
class WorkflowCatalogE2ELiveBase(unittest.TestCase, ABC):

    __test__ = False
    MODEL_PROFILE: ClassVar[str]
    FLOW_START_TOOL: ClassVar[str]

    @property
    @abstractmethod
    def parent_session_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def live_session_runner(self) -> LiveSessionRunning:
        raise NotImplementedError

    def setUp(self) -> None:
        self._temporary_project = tempfile.TemporaryDirectory(prefix="solid-coder-catalog-e2e-")
        self._project_root = Path(self._temporary_project.name)
        workflows = self._project_root / ".solid-coder" / "workflows"
        shutil.copytree(_FIXTURE_ROOT / "workflows", workflows)
        shutil.copyfile(
            _FIXTURE_ROOT / "config.toml",
            self._project_root / ".solid-coder" / "config.toml",
        )
        self._artifact_root = solid_coder_project_dir(self._project_root)

    def tearDown(self) -> None:
        shutil.rmtree(self._artifact_root, ignore_errors=True)
        self._temporary_project.cleanup()

    def test_combined_workflow_resolves_nested_packages_by_id(self) -> None:
        parent_session_id = self.parent_session_id
        profile = ModelProfileLoader(
            project_root=_PLUGIN_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        prompt = (
            f"# spawned-by: {parent_session_id}\n\n"
            f'Call {self.FLOW_START_TOOL} with flow="e2e-catalog-combined". '
            "Drive its confirm_combined step through flow_next with combined=true until it is done. "
            "Do not edit files or call unrelated tools."
        )
        request = LiveSessionRequest(
            prompt=prompt,
            project_root=self._project_root,
            plugin_root=_PLUGIN_ROOT,
            model=profile.llm["model"],
            timeout=profile.llm["timeout"],
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=build_mcp_config(_PLUGIN_ROOT),
        )

        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self._project_root)}):
            with model_profile_environment(profile.profile_path):
                session_result = self.live_session_runner().run(request)

        runs = self._read_runs()
        self.assertEqual(
            len(runs),
            1,
            f"Expected one flow run. Session output: {session_result.final_output}",
        )
        combined_events = self._events_for_flow(runs, "e2e_catalog_combined")

        self._assert_completed_steps(
            combined_events,
            ["first.verify_existing", "second.verify_existing", "confirm_combined"],
        )
        self._assert_successful(combined_events)
        self.assertEqual(self._step_output(combined_events, "first.verify_existing", "existing"), True)
        self.assertEqual(self._step_output(combined_events, "second.verify_existing", "existing"), True)
        self.assertEqual(self._step_output(combined_events, "confirm_combined", "combined"), True)
        self.assertNotEqual(session_result.session_id, parent_session_id)
        self.assertEqual(
            self._model_session_ids(combined_events),
            {session_result.session_id},
        )

    def _read_runs(self) -> list[list[dict]]:
        runs_dir = self._artifact_root / "runs"
        return [
            [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for path in runs_dir.glob("*/events.jsonl")
        ] if runs_dir.exists() else []

    def _events_for_flow(self, runs: list[list[dict]], flow_name: str) -> list[dict]:
        for events in runs:
            if events and events[0].get("flow") == flow_name:
                return events
        self.fail(f"No event log found for flow '{flow_name}'")

    def _assert_completed_steps(self, events: list[dict], expected: list[str]) -> None:
        completed = [
            event.get("step_id", event.get("instance_id"))
            for event in events
            if event.get("event") == "step_completed"
        ]
        self.assertEqual(completed, expected)

    def _assert_successful(self, events: list[dict]) -> None:
        event_types = {event.get("event") for event in events}
        self.assertFalse(event_types & _FAILED_EVENTS)
        self.assertEqual(events[-1].get("event"), "run_completed")

    def _step_output(self, events: list[dict], step_id: str, output_name: str) -> object:
        event = next(
            event
            for event in events
            if event.get("event") == "step_completed" and event.get("step_id") == step_id
        )
        return event["outputs"][output_name]

    def _model_session_ids(self, events: list[dict]) -> set[str]:
        return {
            event["session_id"]
            for event in events
            if event.get("event") == "session_step_recorded"
            and event.get("session_id") != "engine"
        }
