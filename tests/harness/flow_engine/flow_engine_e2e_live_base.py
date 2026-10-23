"""Defines the backend-neutral live flow-engine integration contract."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import textwrap
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

from harness_factory import HookUtilsTomlLoader
from hook_utils import solid_coder_project_dir
from live_session_artifact_scope import LiveSessionArtifactScope
from live_session_request import LiveSessionRequest
from live_session_running import LiveSessionRunning
from mcp_utils import McpConfigBuilder
from model_profile_environment import model_profile_environment
from model_profile_loader import ModelProfileLoader

_PROJECT_ROOT = _MCP_SERVER.parent
_FLOW_PACKAGE = _PROJECT_ROOT / ".solid-coder" / "workflows" / "test" / "e2e-test"
_DYNAMIC_INCLUDE_FLOW = (
    _PROJECT_ROOT
    / ".solid-coder"
    / "workflows"
    / "test"
    / "e2e-dynamic-include"
    / "workflow.yaml"
)
_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_status"
)
_EXPECTED_STEP_PREFIX = [
    "greet",
    "check_environment",
    "count_words",
    "review.draft_review",
    "review.approve_review",
    "prepare_delegations",
    "delegate",
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
solid-spec: [SPEC-031, SPEC-027, SPEC-037, SPEC-054]
solid-description: Executes model-profile-backed routing and session-delegate fan-out while verifying persisted engine transitions.
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

    def test_dynamic_include_materializes_one_child_dag_per_item(self) -> None:
        events = self._run_live_workflow(
            _DYNAMIC_INCLUDE_FLOW,
            prohibited_prompt_fragments=[
                "Alpha inspected",
                "Beta inspected",
                "DYNAMIC WORKFLOW COMPLETE",
            ],
        )
        completed = [
            event for event in events if event.get("event") == "step_completed"
        ]
        completed_step_ids = [event.get("step_id") for event in completed]
        self.assertEqual(
            completed_step_ids,
            [
                "prepare_units",
                "review-1.inspect",
                "review-2.inspect",
                "review-1.report",
                "review-2.report",
                "summarize",
            ],
        )
        included_events = [
            event
            for event in completed
            if str(event.get("step_id", "")).startswith("review-")
        ]
        self.assertEqual(
            [event.get("workflow_source_index") for event in included_events],
            [0, 1, 0, 1],
        )
        self.assertEqual(
            [event.get("workflow_instance_id") for event in included_events],
            ["review-1", "review-2", "review-1", "review-2"],
        )
        self.assertEqual(
            [event.get("local_step_id") for event in included_events],
            ["inspect", "inspect", "report", "report"],
        )
        self.assertEqual(
            [event.get("item") for event in included_events],
            [
                {"name": "Alpha"},
                {"name": "Beta"},
                {"name": "Alpha"},
                {"name": "Beta"},
            ],
        )
        self.assertEqual(
            [event.get("outputs") for event in included_events],
            [
                {"finding": "Alpha inspected"},
                {"finding": "Beta inspected"},
                {"report": "Alpha reported"},
                {"report": "Beta reported"},
            ],
        )
        self.assertEqual(
            completed[-1].get("outputs"),
            {"sentence": "DYNAMIC WORKFLOW COMPLETE"},
        )
        event_types = [event.get("event") for event in events]
        self.assertEqual(event_types[0], "run_started")
        self.assertEqual(event_types[-1], "run_completed")
        self.assertFalse(
            {"step_attempt_failed", "step_rejected", "run_failed"}.intersection(
                event_types
            ),
            event_types,
        )

    def test_collection_backed_metric_is_scored_by_engine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workflow_path = Path(temporary_directory) / "workflow.yaml"
            workflow_path.write_text(
                textwrap.dedent(
                    """
                    id: e2e-collection-metric
                    name: E2E Collection Metric
                    max_turns: 5
                    rule: {}
                    steps:
                      - id: analyze_task_sites
                        prompt: |
                          Submit exactly these four task sites in this order:
                          DETACHED non-exception, STRUCTURED non-exception,
                          DETACHED exception, DETACHED non-exception.
                        outputs:
                          - name: task_sites
                            type: data
                            schema:
                              type: array
                              minItems: 4
                              maxItems: 4
                              items:
                                type: object
                                additionalProperties: false
                                required: [classification, is_exception]
                                properties:
                                  classification:
                                    type: string
                                    enum: [DETACHED, STRUCTURED]
                                  is_exception: {type: boolean}
                      - id: detached_task_count
                        type: metric
                        metric_id: DT-1
                        depends_on: [analyze_task_sites]
                        value: {type: integer, minimum: 0}
                        scoring:
                          source: "{{steps.analyze_task_sites.outputs.task_sites}}"
                          when:
                            all:
                              - ref: "{{item.classification}}"
                                equals: DETACHED
                              - ref: "{{item.is_exception}}"
                                equals: false
                          severe: {operator: greater_than_or_equal, value: 1}
                      - id: classify_exception
                        type: exception
                        depends_on: [detached_task_count]
                        prompt: |
                          Submit is_exception false. Explain that the locked test
                          data is intentionally scored without a whole-rule exception.
                    """
                ),
                encoding="utf-8",
            )

            events = self._run_live_workflow(
                workflow_path,
                prohibited_prompt_fragments=["DETACHED non-exception"],
            )

        metric_completion = next(
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("step_id") == "detached_task_count"
        )
        self.assertEqual(metric_completion["session_id"], "engine")
        self.assertEqual(metric_completion["outputs"]["value"], 2)
        self.assertEqual(
            metric_completion["metric_derivation"]["matched_indexes"],
            [0, 3],
        )
        self.assertEqual(
            metric_completion["metric_derivation"]["excluded_indexes"],
            [1, 2],
        )
        scored = next(
            event for event in events if event.get("event") == "metric_scored"
        )
        self.assertEqual(scored["value"], 2)
        self.assertEqual(scored["severity"], "SEVERE")
        self.assertEqual(scored["raw_severity"], "SEVERE")
        self.assertEqual(
            scored["matching_band"],
            {"operator": "greater_than_or_equal", "value": 1},
        )
        self.assertEqual(scored["derivation"]["source_size"], 4)
        self.assertEqual(events[-1].get("event"), "run_completed")

    def test_collection_reducers_are_scored_and_audited_by_engine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workflow_path = Path(temporary_directory) / "workflow.yaml"
            workflow_path.write_text(
                textwrap.dedent(
                    """
                    id: e2e-collection-reducers
                    name: E2E Collection Reducers
                    max_turns: 5
                    rule: {}
                    steps:
                      - id: classify_observations
                        prompt: |
                          Submit exactly four observations in this order:
                          depth 2, group alpha, UNSAFE, non-exception;
                          depth 9, group beta, UNSAFE, exception;
                          depth 5, group gamma, SAFE, non-exception;
                          depth 7, group gamma, SAFE, exception.
                        outputs:
                          - name: observations
                            type: data
                            schema:
                              type: array
                              minItems: 4
                              maxItems: 4
                              items:
                                type: object
                                additionalProperties: false
                                required:
                                  - depth
                                  - group
                                  - classification
                                  - is_exception
                                properties:
                                  depth: {type: integer}
                                  group: {type: string}
                                  classification:
                                    type: string
                                    enum: [SAFE, UNSAFE]
                                  is_exception: {type: boolean}
                      - id: maximum_depth
                        type: metric
                        metric_id: REDUCER-MAX
                        depends_on: [classify_observations]
                        value: {type: integer, minimum: 0}
                        scoring:
                          source: "{{steps.classify_observations.outputs.observations}}"
                          when:
                            ref: "{{item.is_exception}}"
                            equals: false
                          reducer:
                            type: maximum
                            value: "{{item.depth}}"
                          severe: {operator: greater_than_or_equal, value: 5}
                      - id: minimum_depth
                        type: metric
                        metric_id: REDUCER-MIN
                        depends_on: [classify_observations]
                        value: {type: integer, minimum: 0}
                        scoring:
                          source: "{{steps.classify_observations.outputs.observations}}"
                          when:
                            ref: "{{item.is_exception}}"
                            equals: false
                          reducer:
                            type: minimum
                            value: "{{item.depth}}"
                          severe: {operator: less_than_or_equal, value: 2}
                      - id: distinct_groups
                        type: metric
                        metric_id: REDUCER-DISTINCT
                        depends_on: [classify_observations]
                        value: {type: integer, minimum: 0}
                        scoring:
                          source: "{{steps.classify_observations.outputs.observations}}"
                          when:
                            ref: "{{item.is_exception}}"
                            equals: false
                          reducer:
                            type: distinct_count
                            value: "{{item.group}}"
                          severe: {operator: greater_than_or_equal, value: 2}
                      - id: unsafe_ratio
                        type: metric
                        metric_id: REDUCER-RATIO
                        depends_on: [classify_observations]
                        value: {type: number, minimum: 0, maximum: 1}
                        scoring:
                          source: "{{steps.classify_observations.outputs.observations}}"
                          reducer:
                            type: ratio
                            numerator_when:
                              all:
                                - ref: "{{item.classification}}"
                                  equals: UNSAFE
                                - ref: "{{item.is_exception}}"
                                  equals: false
                            denominator_when:
                              ref: "{{item.is_exception}}"
                              equals: false
                          severe: {operator: greater_than_or_equal, value: 0.5}
                      - id: classify_exception
                        type: exception
                        depends_on:
                          - maximum_depth
                          - minimum_depth
                          - distinct_groups
                          - unsafe_ratio
                        prompt: |
                          Submit is_exception false. Explain that the locked test
                          data is intentionally scored without a whole-rule exception.
                    """
                ),
                encoding="utf-8",
            )

            events = self._run_live_workflow(
                workflow_path,
                prohibited_prompt_fragments=["group alpha"],
            )

        metric_completions = {
            event["step_id"]: event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("step_id")
            in {
                "maximum_depth",
                "minimum_depth",
                "distinct_groups",
                "unsafe_ratio",
            }
        }
        self.assertEqual(
            set(metric_completions),
            {
                "maximum_depth",
                "minimum_depth",
                "distinct_groups",
                "unsafe_ratio",
            },
        )
        self.assertEqual(
            {
                step_id: completion["outputs"]["value"]
                for step_id, completion in metric_completions.items()
            },
            {
                "maximum_depth": 5,
                "minimum_depth": 2,
                "distinct_groups": 2,
                "unsafe_ratio": 0.5,
            },
        )
        self.assertEqual(
            {
                step_id: completion["metric_derivation"]["reducer"]["type"]
                for step_id, completion in metric_completions.items()
            },
            {
                "maximum_depth": "maximum",
                "minimum_depth": "minimum",
                "distinct_groups": "distinct_count",
                "unsafe_ratio": "ratio",
            },
        )
        self.assertTrue(
            all(
                completion["session_id"] == "engine"
                for completion in metric_completions.values()
            )
        )

        maximum_derivation = metric_completions["maximum_depth"]["metric_derivation"]
        self.assertEqual(maximum_derivation["kind"], "collection_reducer")
        self.assertEqual(maximum_derivation["matched_indexes"], [0, 2])
        self.assertEqual(maximum_derivation["excluded_indexes"], [1, 3])
        self.assertEqual(
            maximum_derivation["projection_evidence"],
            [{"index": 0, "value": 2}, {"index": 2, "value": 5}],
        )
        ratio_derivation = metric_completions["unsafe_ratio"]["metric_derivation"]
        self.assertEqual(ratio_derivation["numerator_indexes"], [0])
        self.assertEqual(ratio_derivation["denominator_indexes"], [0, 2])
        self.assertFalse(ratio_derivation["zero_denominator"])

        scored = {
            event["metric_id"]: event
            for event in events
            if event.get("event") == "metric_scored"
        }
        self.assertEqual(
            {metric_id: decision["value"] for metric_id, decision in scored.items()},
            {
                "REDUCER-MAX": 5,
                "REDUCER-MIN": 2,
                "REDUCER-DISTINCT": 2,
                "REDUCER-RATIO": 0.5,
            },
        )
        self.assertTrue(
            all(decision["severity"] == "SEVERE" for decision in scored.values())
        )
        self.assertEqual(events[-1].get("event"), "run_completed")

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
        events = self._run_live_workflow(
            workflow_path,
            prohibited_prompt_fragments=[case.text, case.expected_sentence],
        )
        event_types = [event.get("event") for event in events]
        completed_sequence = [
            event.get("step_id", event.get("instance_id"))
            for event in events
            if event.get("event") == "step_completed"
        ]
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
        delegated_sessions = self._matching_step_events(
            events,
            event_type="step_completed",
            step_id="delegate",
        )
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
        self.assertEqual(len(delegated_sessions), 2, event_types)
        ordered_delegated_sessions = sorted(
            delegated_sessions,
            key=lambda event: event["iteration_index"],
        )
        self.assertEqual(
            [event["iteration_index"] for event in ordered_delegated_sessions],
            [0, 1],
        )
        self.assertEqual(
            [event["outputs"]["child_value"] for event in ordered_delegated_sessions],
            [42, 42],
        )
        self.assertEqual(
            {event["session_id"] for event in delegated_sessions},
            {"engine"},
        )
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
        self.assertEqual(event_types[-1], "run_completed", event_types)

    def _run_live_workflow(
        self,
        workflow_path: Path,
        prohibited_prompt_fragments: list[str],
    ) -> list[dict]:
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
        for fragment in prohibited_prompt_fragments:
            self.assertNotIn(fragment, prompt)
        request = LiveSessionRequest(
            prompt=prompt,
            artifact_scope=LiveSessionArtifactScope(
                domain="flow-engine",
                scenario="workflow-contract",
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

        after = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        new_logs = after - before
        self.assertTrue(
            new_logs,
            "No new events.jsonl appeared after the session. "
            f"Session result: {session_result.final_output}",
        )
        events_path = max(new_logs, key=lambda path: path.stat().st_mtime)
        preserved_workflow = session_result.artifact_directory / "workflow"
        shutil.copytree(workflow_path.parent, preserved_workflow)
        preserved_events_path = session_result.artifact_directory / "flow-events.jsonl"
        shutil.copy2(events_path, preserved_events_path)
        events = [
            json.loads(line)
            for line in preserved_events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(preserved_workflow.joinpath(workflow_path.name).is_file())
        self.assertEqual(
            preserved_events_path.read_bytes(),
            events_path.read_bytes(),
        )
        model_session_ids = {
            event.get("session_id")
            for event in events
            if event.get("event") == "session_step_recorded"
            and event.get("session_id") != "engine"
        }
        self.assertNotEqual(session_result.session_id, parent_session_id)
        self.assertEqual(
            model_session_ids,
            {session_result.session_id},
            f"Events: {events}\n\nSession output: {session_result.final_output}",
        )
        print(
            f"\nLive flow artifacts: {session_result.artifact_directory}\n",
            flush=True,
        )
        return events

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
        self.assertEqual(skipped[0]["evidence"]["kind"], "comparison")
        self.assertFalse(skipped[0]["evidence"]["matched"])
        self.assertTrue(skipped[0]["evidence"]["actual"]["present"])
