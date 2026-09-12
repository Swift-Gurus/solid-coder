"""Defines the backend-neutral live flow-session scoping contract."""

from __future__ import annotations

import sys
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

_HARNESS_DIR = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
_MCP_HEALTH_CONFIG = _MCP_SERVER / "health" / "config"
for _directory in (_HARNESS_DIR, _MCP_SERVER, _MCP_HEALTH_CONFIG):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness_factory import HookUtilsTomlLoader  # noqa: E402
from hook_utils import solid_coder_project_dir  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_running import LiveSessionRunning  # noqa: E402
from mcp_utils import McpConfigBuilder  # noqa: E402
from model_profile_environment import model_profile_environment  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402

_PROJECT_ROOT = _MCP_SERVER.parent
_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__solid-coder-pipeline__flow_start,flow_start"
)


"""
solid-name: FlowSessionScopingE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-031]
solid-description: Starts one live flow and verifies its active pointer or completed events are scoped to the child session reported by the selected backend adapter.
"""
class FlowSessionScopingE2ELiveBase(unittest.TestCase, ABC):

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
        self._clear_active_pointers()

    def tearDown(self) -> None:
        self._clear_active_pointers()

    def test_run_state_matches_child_session_id(self) -> None:
        runs_directory = self._runs_dir()
        event_logs_before = set(runs_directory.glob("*/events.jsonl"))
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        request = LiveSessionRequest(
            prompt=(
                f"# spawned-by: {self.parent_session_id}\n\n"
                f'Call {self.FLOW_START_TOOL} exactly once with flow="e2e-test". '
                "Immediately stop after that tool returns; do not call another tool."
            ),
            artifact_scope=LiveSessionArtifactScope(
                domain="flow-engine",
                scenario="session-scoping",
            ),
            project_root=_PROJECT_ROOT,
            plugin_root=_PROJECT_ROOT,
            model=profile.llm["model"],
            timeout=profile.llm["timeout"],
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=McpConfigBuilder().build(_PROJECT_ROOT),
        )
        with model_profile_environment(profile.profile_path):
            session_result = self.live_session_runner().run(request)

        expected_pointer = runs_directory / f"active-{session_result.session_id}.json"
        self.assertFalse((runs_directory / "active.json").exists())
        if expected_pointer.exists():
            return

        new_event_logs = set(runs_directory.glob("*/events.jsonl")) - event_logs_before
        child_session_marker = f'"session_id": "{session_result.session_id}"'
        child_owned_logs = [
            path
            for path in new_event_logs
            if child_session_marker in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            len(child_owned_logs),
            1,
            "No active pointer or completed run events matched the child session ID. "
            f"Child: {session_result.session_id}; output: {session_result.final_output}",
        )
        self.assertIn(
            '"event": "run_completed"',
            child_owned_logs[0].read_text(encoding="utf-8"),
        )

    def _runs_dir(self) -> Path:
        return solid_coder_project_dir(_PROJECT_ROOT) / "runs"

    def _clear_active_pointers(self) -> None:
        runs_dir = self._runs_dir()
        if not runs_dir.exists():
            return
        for pointer in runs_dir.glob("active*.json"):
            pointer.unlink(missing_ok=True)
