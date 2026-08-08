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
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_running import LiveSessionRunning  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402
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
solid-description: Starts one live flow and verifies its active pointer is scoped to the child session reported by the selected backend adapter.
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

    def test_active_pointer_matches_child_session_id(self) -> None:
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        request = LiveSessionRequest(
            prompt=(
                f"# spawned-by: {self.parent_session_id}\n\n"
                f'Call {self.FLOW_START_TOOL} exactly once with flow="e2e_test". '
                "Immediately stop after that tool returns; do not call another tool."
            ),
            project_root=_PROJECT_ROOT,
            plugin_root=_PROJECT_ROOT,
            model=profile.llm["model"],
            timeout=profile.llm["timeout"],
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=build_mcp_config(_PROJECT_ROOT),
        )
        with model_profile_environment(profile.profile_path):
            session_result = self.live_session_runner().run(request)

        expected_pointer = self._runs_dir() / f"active-{session_result.session_id}.json"
        self.assertTrue(
            expected_pointer.exists(),
            "No active pointer matched the child session ID. "
            f"Child: {session_result.session_id}; output: {session_result.final_output}",
        )
        self.assertFalse((self._runs_dir() / "active.json").exists())

    def _runs_dir(self) -> Path:
        return solid_coder_project_dir(_PROJECT_ROOT) / "runs"

    def _clear_active_pointers(self) -> None:
        runs_dir = self._runs_dir()
        if not runs_dir.exists():
            return
        for pointer in runs_dir.glob("active*.json"):
            pointer.unlink(missing_ok=True)
