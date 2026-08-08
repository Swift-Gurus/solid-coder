"""Defines the backend-neutral live SRP workflow contract."""

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
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "SRP" / "fixtures" / "fixture-1.swift"
_EXPECTATION = _PROJECT_ROOT / "tests" / "principles" / "SRP" / "expectations" / "fixture-1.json"
_UNIT_NAME = "ProductCatalog"
_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_status"
)
_EXPECTED_STEP_OUTPUTS = {
    "measure_verbs": ("verb_count", "verb_evidence", 6),
    "measure_cohesion": ("cohesion_groups", "cohesion_evidence", 2),
    "measure_stakeholders": ("stakeholder_count", "stakeholder_evidence", 2),
}


"""
solid-name: SRPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-034]
solid-description: Runs the same exact SRP workflow assertions through any model-profile-backed live session.
"""
class SRPValidationE2ELiveBase(unittest.TestCase, ABC):

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

    def test_fixture_completes_with_exact_metrics_and_findings(self) -> None:
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        params = {
            "code": _FIXTURE.read_text(encoding="utf-8"),
            "file_path": str(_FIXTURE),
            "unit_name": _UNIT_NAME,
            "unit_kind": "class",
            "timestamp": "2026-08-02T20:00:00Z",
        }
        parent_session_id = self.parent_session_id
        prompt = (
            f"# spawned-by: {parent_session_id}\n\n"
            f'Call {self.FLOW_START_TOOL} with flow="srp_validation" and params equal to this JSON. '
            "Drive every returned step with flow_next until the flow reaches done. Do not edit files: "
            f"{json.dumps(params)}"
        )
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
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
            "No flow event log was created. "
            f"Session output: {session_result.final_output}",
        )
        events_path = max(new_logs, key=lambda path: path.stat().st_mtime)
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self._assert_events(events, session_result.session_id, parent_session_id)

    def _assert_events(
        self,
        events: list[dict],
        child_session_id: str,
        parent_session_id: str,
    ) -> None:
        completed_steps = [event for event in events if event.get("event") == "step_completed"]
        metric_steps = completed_steps[:-1]
        score_event = completed_steps[-1]

        self.assertEqual(events[-1]["event"], "run_completed")
        self.assertFalse(
            {event.get("event") for event in events}
            & {"step_attempt_failed", "step_rejected", "run_failed"}
        )
        self.assertEqual({event["step_id"] for event in metric_steps}, set(_EXPECTED_STEP_OUTPUTS))
        self.assertEqual(score_event["step_id"], "score_results")
        metric_outputs = {event["step_id"]: event["outputs"] for event in metric_steps}
        for step_id, expectation in _EXPECTED_STEP_OUTPUTS.items():
            metric_name, evidence_name, expected_value = expectation
            outputs = metric_outputs[step_id]
            self.assertEqual(outputs[metric_name], expected_value)
            self.assertEqual(len(outputs[evidence_name]), expected_value)

        recorded_sessions = [
            event for event in events if event.get("event") == "session_step_recorded"
        ]
        self.assertEqual(
            {event["instance_id"] for event in recorded_sessions},
            {"measure_verbs-1", "measure_cohesion-1", "measure_stakeholders-1", "score_results-1"},
        )
        model_session_ids = {
            event.get("session_id")
            for event in recorded_sessions
            if event.get("session_id") != "engine"
        }
        self.assertNotEqual(child_session_id, parent_session_id)
        self.assertEqual(model_session_ids, {child_session_id})

        scored_unit = score_event["outputs"]["scored_review"]["results"][0]["files"][0]["units"][0]
        scored_metrics = {
            name: value["value"]
            for name, value in scored_unit["metrics"]["SRP"].items()
        }
        self.assertEqual(
            scored_metrics,
            {"verb_count": 6, "cohesion_groups": 2, "stakeholder_count": 2},
        )
        actual_findings = {
            (scored_unit["unit_name"], violation["rule_id"], violation["severity"])
            for violation in scored_unit["violations"]
        }
        expected_entries = json.loads(_EXPECTATION.read_text(encoding="utf-8"))["findings"]
        expected_findings = {
            (entry["unit_name"], entry["metric_id"], entry["severity"])
            for entry in expected_entries
        }
        self.assertEqual(actual_findings, expected_findings)
        for entry in expected_entries:
            for metric_name, expected_value in entry.get("metrics", {}).items():
                self.assertEqual(scored_metrics[metric_name], expected_value)
