"""Exercises co-located metric derivation through live model sessions."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

_HARNESS_DIR = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
_MCP_HEALTH_CONFIG = _MCP_SERVER / "health" / "config"
for _directory in [_HARNESS_DIR, _MCP_SERVER, _MCP_HEALTH_CONFIG]:
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from harness_factory import HookUtilsTomlLoader  # noqa: E402
from hook_utils import solid_coder_project_dir  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_running import LiveSessionRunning  # noqa: E402
from mcp_utils import McpConfigBuilder  # noqa: E402
from model_profile_environment import model_profile_environment  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402

_PROJECT_ROOT = _MCP_SERVER.parent


"""
solid-name: CoLocatedMetricE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-058]
solid-description: Runs one test-owned live agent step and proves MCP derives two co-located metrics from its single observation submission.
"""
class CoLocatedMetricE2ELiveBase(unittest.TestCase, ABC):

    __test__ = False
    MODEL_PROFILE: ClassVar[str]
    ALLOWED_FLOW_TOOLS: ClassVar[str]

    @property
    @abstractmethod
    def parent_session_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def flow_execution_instruction(
        self,
        workflow_id: str,
        parameters_json: str,
    ) -> str:
        raise NotImplementedError

    def live_session_runner(self) -> LiveSessionRunning:
        raise NotImplementedError

    def setUp(self) -> None:
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        if runs_dir.exists():
            for pointer in runs_dir.glob("active*.json"):
                pointer.unlink(missing_ok=True)

    def test_derives_two_metrics_from_one_observation_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workflow_path = Path(temporary_directory) / "workflow.yaml"
            workflow_path.write_text(
                textwrap.dedent(self._workflow()),
                encoding="utf-8",
            )

            events = self._run_live_workflow(workflow_path)

        completed = [
            event
            for event in events
            if event.get("event") == "step_completed"
        ]
        completed_by_step = {
            event["step_id"]: event
            for event in completed
        }
        self.assertEqual(
            [event["step_id"] for event in completed],
            [
                "classify_actions",
                "action_count",
                "total_count",
                "classify_exception",
            ],
        )
        self.assertEqual(completed_by_step["action_count"]["outputs"]["value"], 2)
        self.assertEqual(completed_by_step["total_count"]["outputs"]["value"], 3)
        self.assertEqual(
            completed_by_step["action_count"]["metric_derivation"]["matched_indexes"],
            [1, 2],
        )
        self.assertEqual(
            completed_by_step["total_count"]["metric_derivation"]["matched_indexes"],
            [0, 1, 2],
        )
        self.assertEqual(
            len([
                event
                for event in completed
                if event.get("session_id") != "engine"
            ]),
            2,
        )
        self.assertFalse(
            {
                "step_attempt_failed",
                "step_rejected",
                "run_failed",
            }.intersection(event.get("event") for event in events),
            events,
        )
        self.assertEqual(events[-1].get("event"), "run_completed")

    def _run_live_workflow(self, workflow_path: Path) -> list[dict]:
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        request = LiveSessionRequest(
            prompt=(
                f"# spawned-by: {self.parent_session_id}\n\n"
                + self.flow_execution_instruction(str(workflow_path), "{}")
            ),
            artifact_scope=LiveSessionArtifactScope(
                domain="flow-engine",
                scenario="co-located-metric",
            ),
            project_root=_PROJECT_ROOT,
            plugin_root=_PROJECT_ROOT,
            model=profile.llm["model"],
            timeout=profile.llm["timeout"],
            allowed_tools=self.ALLOWED_FLOW_TOOLS,
            mcp_config=McpConfigBuilder().build(_PROJECT_ROOT),
        )
        with model_profile_environment(profile.profile_path):
            session_result = self.live_session_runner().run(request)

        after = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        new_logs = after - before
        self.assertTrue(
            new_logs,
            "No flow events were persisted. "
            f"Session result: {session_result.final_output}",
        )
        events_path = max(new_logs, key=lambda path: path.stat().st_mtime)
        preserved_workflow = session_result.artifact_directory / "workflow.yaml"
        preserved_events = session_result.artifact_directory / "flow-events.jsonl"
        shutil.copy2(workflow_path, preserved_workflow)
        shutil.copy2(events_path, preserved_events)
        events = [
            json.loads(line)
            for line in preserved_events.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        model_session_ids = {
            event.get("session_id")
            for event in events
            if event.get("event") == "session_step_recorded"
            and event.get("session_id") != "engine"
        }
        self.assertNotEqual(session_result.session_id, self.parent_session_id)
        self.assertEqual(model_session_ids, {session_result.session_id})
        print(
            f"\nCo-located metric live artifacts: "
            f"{session_result.artifact_directory}\n",
            flush=True,
        )
        return events

    @staticmethod
    def _workflow() -> str:
        return """
        id: co-located-metric-live
        name: Co-Located Metric Live Contract
        max_turns: 2
        rule: {}
        steps:
          - id: classify_actions
            type: agent
            prompt: |
              Submit exactly these three observations as the `actions` output:

              - name: initialize
                is_lifecycle: true
              - name: load
                is_lifecycle: false
              - name: save
                is_lifecycle: false

              Do not calculate or submit any metric.
            outputs:
              - name: actions
                type: data
                schema:
                  type: array
                  minItems: 3
                  maxItems: 3
                  items:
                    type: object
                    additionalProperties: false
                    required: [name, is_lifecycle]
                    properties:
                      name: {type: string}
                      is_lifecycle: {type: boolean}
            metrics:
              - id: action_count
                metric_id: LIVE-ACTIONS
                value: {type: integer, minimum: 0}
                scoring:
                  source: actions
                  when:
                    ref: "{{item.is_lifecycle}}"
                    equals: false
                  severe: {operator: greater_than_or_equal, value: 2}
              - id: total_count
                metric_id: LIVE-TOTAL
                value: {type: integer, minimum: 0}
                scoring:
                  source: actions
                  severe: {operator: greater_than_or_equal, value: 3}
          - id: classify_exception
            type: exception
            depends_on: [action_count, total_count]
            prompt: |
              Submit `is_exception` as false. Explain that this locked live
              fixture intentionally exercises deterministic metric derivation.
        """


class TestCodexCoLocatedMetricE2ELive(CodexTestBase, CoLocatedMetricE2ELiveBase):

    __test__ = True


class TestClaudeCoLocatedMetricE2ELive(ClaudeTestBase, CoLocatedMetricE2ELiveBase):

    __test__ = True


if __name__ == "__main__":
    unittest.main()
