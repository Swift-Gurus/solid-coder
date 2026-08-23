"""Provides backend-neutral execution and evidence preservation for live workflows."""

from __future__ import annotations

import json
import shutil
import sys
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

_HARNESS_DIRECTORY = Path(__file__).resolve().parent
_MCP_SERVER_DIRECTORY = _HARNESS_DIRECTORY.parents[1] / "mcp-server"
_MCP_HEALTH_CONFIG_DIRECTORY = _MCP_SERVER_DIRECTORY / "health" / "config"
for _directory in (
    _HARNESS_DIRECTORY,
    _MCP_SERVER_DIRECTORY,
    _MCP_HEALTH_CONFIG_DIRECTORY,
):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness_factory import HookUtilsTomlLoader
from hook_utils import solid_coder_project_dir
from live_session_request import LiveSessionRequest
from live_session_running import LiveSessionRunning
from live_workflow_scenario import LiveWorkflowScenario
from mcp_config_builder import build_mcp_config
from model_profile_environment import model_profile_environment
from model_profile_loader import ModelProfileLoader
from preserved_live_workflow_run import PreservedLiveWorkflowRun


_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_status"
)


"""
solid-name: LiveWorkflowE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Executes any typed workflow scenario through a selected live model backend and recursively preserves its canonical MCP run for scenario-specific assertions.
"""
class LiveWorkflowE2ELiveBase(unittest.TestCase, ABC):

    __test__ = False
    MODEL_PROFILE: ClassVar[str]
    FLOW_START_TOOL: ClassVar[str]
    PROJECT_ROOT: ClassVar[Path]

    @property
    @abstractmethod
    def parent_session_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def scenario(self) -> LiveWorkflowScenario:
        raise NotImplementedError

    @abstractmethod
    def live_session_runner(self) -> LiveSessionRunning:
        raise NotImplementedError

    @abstractmethod
    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        raise NotImplementedError

    @property
    def execution_project_root(self) -> Path:
        return self.PROJECT_ROOT

    def setUp(self) -> None:
        runs_directory = self._runs_directory()
        if runs_directory.exists():
            for pointer in runs_directory.glob("active*.json"):
                pointer.unlink(missing_ok=True)

    def test_workflow_satisfies_its_live_contract(self) -> None:
        self.assert_workflow(self._run_scenario(self.scenario))

    def _run_scenario(
        self,
        scenario: LiveWorkflowScenario,
    ) -> PreservedLiveWorkflowRun:
        runs_directory = self._runs_directory()
        before = (
            set(runs_directory.glob("*/events.jsonl"))
            if runs_directory.exists()
            else set()
        )
        profile = ModelProfileLoader(
            project_root=self.PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        request = LiveSessionRequest(
            prompt=self._prompt(scenario),
            artifact_scope=scenario.artifact_scope,
            project_root=self.execution_project_root,
            plugin_root=self.PROJECT_ROOT,
            model=profile.llm["model"],
            timeout=profile.llm["timeout"],
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=build_mcp_config(self.PROJECT_ROOT),
        )

        with model_profile_environment(profile.profile_path):
            session = self.live_session_runner().run(request)

        after = (
            set(runs_directory.glob("*/events.jsonl"))
            if runs_directory.exists()
            else set()
        )
        new_event_logs = after - before
        self.assertTrue(
            new_event_logs,
            f"No flow event log was created. Session output: {session.final_output}",
        )
        events_path = max(new_event_logs, key=lambda path: path.stat().st_mtime)
        preserved_run_directory = session.artifact_directory / "flow-run"
        shutil.copytree(events_path.parent, preserved_run_directory)
        self._assert_exact_copy(events_path.parent, preserved_run_directory)
        preserved_run = PreservedLiveWorkflowRun(
            session=session,
            run_directory=preserved_run_directory,
        )
        self._assert_session_ownership(preserved_run)
        return preserved_run

    def _prompt(self, scenario: LiveWorkflowScenario) -> str:
        return (
            f"# spawned-by: {self.parent_session_id}\n\n"
            f"Call {self.FLOW_START_TOOL} with flow={json.dumps(scenario.workflow_id)} "
            f"and params equal to this JSON: {scenario.parameters.model_dump_json()}. "
            "Drive every returned step with flow_next until the flow reaches done, "
            "failed, or timed out. Do not edit files."
        )

    def _runs_directory(self) -> Path:
        return solid_coder_project_dir(self.execution_project_root) / "runs"

    def _assert_session_ownership(self, run: PreservedLiveWorkflowRun) -> None:
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        model_session_ids = {
            event.get("session_id")
            for event in events
            if event.get("event") == "session_step_recorded"
            and event.get("session_id") != "engine"
        }
        self.assertNotEqual(run.session.session_id, self.parent_session_id)
        self.assertEqual(model_session_ids, {run.session.session_id})

    def _assert_exact_copy(self, source: Path, preserved: Path) -> None:
        source_files = sorted(
            path.relative_to(source)
            for path in source.rglob("*")
            if path.is_file()
        )
        preserved_files = sorted(
            path.relative_to(preserved)
            for path in preserved.rglob("*")
            if path.is_file()
        )
        self.assertEqual(preserved_files, source_files)
        for relative_path in source_files:
            self.assertEqual(
                (preserved / relative_path).read_bytes(),
                (source / relative_path).read_bytes(),
            )
