"""Defines the backend-neutral live flow-engine integration contract."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from abc import ABC, abstractmethod
from dataclasses import dataclass
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
_FLOW_PACKAGE = (
    _PROJECT_ROOT / ".solid-coder" / "workflows" / "test" / "e2e-test"
)
_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_status,Task"
)
_EXPECTED_STEP_PREFIX = [
    "greet",
    "check_environment",
    "count_words",
    "review.draft_review",
    "review.approve_review",
    "delegate",
]


@dataclass(frozen=True)
class ClassificationCase:
    text: str
    expected_category: str
    completed_branch: str
    skipped_branch: str
    expected_sentence: str


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

    def test_question_prompt_selects_question_branch(self) -> None:
        self._run_classification_case(
            ClassificationCase(
                text="Is the deployment ready?",
                expected_category="question",
                completed_branch="respond_question",
                skipped_branch="respond_statement",
                expected_sentence="QUESTION CATEGORY SELECTED",
            )
        )

    def test_statement_prompt_selects_statement_branch(self) -> None:
        self._run_classification_case(
            ClassificationCase(
                text="The deployment is ready.",
                expected_category="statement",
                completed_branch="respond_statement",
                skipped_branch="respond_question",
                expected_sentence="STATEMENT CATEGORY SELECTED",
            )
        )

    def _run_classification_case(self, case: ClassificationCase) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workflow_package = Path(temporary_directory) / "flows"
            shutil.copytree(_FLOW_PACKAGE, workflow_package)
            self._write_classification_prompt(workflow_package, case.text)
            self._run_workflow_case(workflow_package / "workflow.yaml", case)

    def _write_classification_prompt(
        self,
        workflow_package: Path,
        classification_text: str,
    ) -> None:
        prompt = (
            "Classify the text below as exactly `question` or `statement`.\n\n"
            "Use `question` when the text asks for information. Use `statement` "
            "when it asserts information without asking for an answer.\n\n"
            "Submit only the selected value as the `category` output field.\n\n"
            f"Text:\n{classification_text}\n"
        )
        (workflow_package / "prompts" / "classify.md").write_text(
            prompt,
            encoding="utf-8",
        )

    def _run_workflow_case(
        self,
        workflow_path: Path,
        case: ClassificationCase,
    ) -> None:
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        parent_session_id = self.parent_session_id
        prompt = (
            f"# spawned-by: {parent_session_id}\n\n"
            f'Call {self.FLOW_START_TOOL} with flow="{workflow_path}". '
            "Drive every returned step through flow_next until the flow reports done, "
            "failed, or timed out."
        )
        self.assertNotIn(case.text, prompt)
        self.assertNotIn(case.expected_sentence, prompt)
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
        classification_event = next(
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("step_id") == "classify"
        )
        completed_branch_event = next(
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("step_id") == case.completed_branch
        )
        skipped_branch_events = [
            event
            for event in events
            if event.get("event") == "step_skipped"
            and event.get("step_id") == case.skipped_branch
        ]
        completed_prefix = [
            *_EXPECTED_STEP_PREFIX,
            "classify",
            case.completed_branch,
        ]
        question_unit_completed = self._matching_step_events(
            events,
            event_type="step_completed",
            step_id="handle_question_units",
        )
        question_unit_skipped = self._matching_step_events(
            events,
            event_type="step_skipped",
            step_id="handle_question_units",
        )
        statement_unit_completed = self._matching_step_events(
            events,
            event_type="step_completed",
            step_id="handle_statement_units",
        )
        statement_unit_skipped = self._matching_step_events(
            events,
            event_type="step_skipped",
            step_id="handle_statement_units",
        )
        self.assertEqual(event_types[0], "run_started", event_types)
        self.assertEqual(completed_sequence[: len(completed_prefix)], completed_prefix)
        self.assertEqual(completed_sequence[-1], "summarize", event_types)
        self.assertEqual(completed_sequence.count("prepare_units"), 1, event_types)
        self.assertEqual(
            classification_event["outputs"]["category"],
            case.expected_category,
        )
        self.assertEqual(
            completed_branch_event["outputs"]["sentence"],
            case.expected_sentence,
        )
        self.assertEqual(len(skipped_branch_events), 1, event_types)
        self._assert_unit_route(
            completed=question_unit_completed,
            skipped=question_unit_skipped,
            completed_index=0,
            skipped_index=1,
            expected_sentence="QUESTION UNIT SELECTED",
        )
        self._assert_unit_route(
            completed=statement_unit_completed,
            skipped=statement_unit_skipped,
            completed_index=1,
            skipped_index=0,
            expected_sentence="STATEMENT UNIT SELECTED",
        )
        self.assertFalse(
            {"step_attempt_failed", "step_rejected", "run_failed"}.intersection(
                event_types
            ),
            event_types,
        )
        self.assertNotEqual(session_result.session_id, parent_session_id)
        self.assertEqual(model_session_ids, {session_result.session_id})
        self.assertEqual(event_types[-1], "run_completed", event_types)

    def _matching_step_events(
        self,
        events: list[dict],
        event_type: str,
        step_id: str,
    ) -> list[dict]:
        return [
            event
            for event in events
            if event.get("event") == event_type and event.get("step_id") == step_id
        ]

    def _assert_unit_route(
        self,
        completed: list[dict],
        skipped: list[dict],
        completed_index: int,
        skipped_index: int,
        expected_sentence: str,
    ) -> None:
        self.assertEqual(len(completed), 1)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(completed[0]["iteration_index"], completed_index)
        self.assertEqual(skipped[0]["iteration_index"], skipped_index)
        self.assertEqual(completed[0]["outputs"]["sentence"], expected_sentence)
