"""Defines the backend-neutral live flow-engine integration contract."""

from __future__ import annotations

import json
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
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_status,Task"
)
_EXPECTED_STEP_SEQUENCE = [
    "greet",
    "check_environment",
    "count_words",
    "review.draft_review",
    "review.approve_review",
    "delegate",
    "summarize",
]


"""
solid-name: FlowEngineE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-031, SPEC-027]
solid-description: Executes one model-profile-backed flow session and verifies the complete persisted engine transition sequence.
"""
class FlowEngineE2ELiveBase(unittest.TestCase, ABC):

    __test__ = False
    MODEL_PROFILE: ClassVar[str]
    FLOW_START_TOOL: ClassVar[str]

    @property
    @abstractmethod
    def parent_session_id(self) -> str:
        raise NotImplementedError

    def live_session_runner(self) -> LiveSessionRunning:
        raise NotImplementedError

    def setUp(self) -> None:
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        if runs_dir.exists():
            for pointer in runs_dir.glob("active*.json"):
                pointer.unlink(missing_ok=True)

    def test_flow_reaches_done_with_expected_transitions(self) -> None:
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        parent_session_id = self.parent_session_id
        prompt = (
            f"# spawned-by: {parent_session_id}\n\n"
            f'Call {self.FLOW_START_TOOL} with flow="e2e_test".'
        )
        request = LiveSessionRequest(
            prompt=prompt,
            project_root=_PROJECT_ROOT,
            plugin_root=_PROJECT_ROOT,
            model=profile.llm["model"],
            timeout=profile.llm["timeout"],
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=build_mcp_config(_PROJECT_ROOT),
        )
        with model_profile_environment(profile.profile_path):
            session_result = self.live_session_runner().run(request)

        after = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        new_logs = after - before
        self.assertTrue(
            new_logs,
            "No new events.jsonl appeared after the session. "
            f"Session result: {session_result.final_output}",
        )
        events_path = max(new_logs, key=lambda path: path.stat().st_mtime)
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        event_types = [event.get("event") for event in events]
        completed_sequence = [
            event.get("step_id", event.get("instance_id"))
            for event in events
            if event.get("event") == "step_completed"
        ]
        model_session_ids = {
            event.get("session_id")
            for event in events
            if event.get("event") == "session_step_recorded"
            and event.get("session_id") != "engine"
        }
        self.assertEqual(event_types[0], "run_started", event_types)
        self.assertEqual(completed_sequence, _EXPECTED_STEP_SEQUENCE, event_types)
        self.assertNotEqual(session_result.session_id, parent_session_id)
        self.assertEqual(model_session_ids, {session_result.session_id})
        self.assertEqual(event_types[-1], "run_completed", event_types)
