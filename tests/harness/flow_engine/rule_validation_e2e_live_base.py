"""Defines shared live assertions for one executable review-rule workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import ClassVar

_HARNESS_DIR = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
for _directory in (_HARNESS_DIR, _MCP_SERVER):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness.review_result import ReviewResult  # noqa: E402
from harness.rule_review_result import RuleReviewResult  # noqa: E402
from review.prepare_review_input import PrepareReviewInput  # noqa: E402
from source.file_analysis_source import FileAnalysisSource  # noqa: E402
from bundled_review_rule_policy_writer import (  # noqa: E402
    BundledReviewRulePolicyWriter,
)
from codex_protocol.reader import CodexProtocolReader  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_rule_validation_expectation import (  # noqa: E402
    LiveRuleValidationExpectation,
)
from live_workflow_e2e_live_base import LiveWorkflowE2ELiveBase  # noqa: E402
from live_workflow_scenario import LiveWorkflowScenario  # noqa: E402
from preserved_live_workflow_run import PreservedLiveWorkflowRun  # noqa: E402
from review_comparison_source_project import (  # noqa: E402
    ReviewComparisonSourceProject,
)
from rule_metric_result_expectation import RuleMetricResultExpectation  # noqa: E402


_PROJECT_ROOT = _MCP_SERVER.parent


"""
solid-name: RuleValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Applies one backend-neutral event, observation, scoring, exception, and artifact contract to executable review rules.
"""
class RuleValidationE2ELiveBase(LiveWorkflowE2ELiveBase):
    PROJECT_ROOT = _PROJECT_ROOT

    WORKFLOW_ID: ClassVar[str]
    ARTIFACT_SCENARIO: ClassVar[str]
    FIXTURE: ClassVar[Path]
    EXPECTED_STEP_IDS: ClassVar[list[str]]
    EXPECTED_ANALYSIS_STEP_IDS: ClassVar[list[str]] = []
    EXPECTED_METRIC_IDS: ClassVar[list[str]]
    EXPECTED_OBSERVATION_IDS: ClassVar[list[str] | None] = None
    EXPECTED_VALUES: ClassVar[list[int | float | str | bool]]
    EXPECTED_METRIC_SEVERITIES: ClassVar[list[str]]
    EXPECTED_FINAL_SEVERITY: ClassVar[str]
    REVIEW_WORKFLOW_ID: ClassVar[str] = "solid-review"
    EXPECTED_EXCEPTION: ClassVar[bool] = False
    ALLOW_AUXILIARY_STEPS: ClassVar[bool] = False
    EXPECTED_RULE_SOURCE_INDEX: ClassVar[int] = 0
    EXPECTED_RULE_RESULT_COUNT: ClassVar[int] = 1

    def setUp(self) -> None:
        self._source_project = ReviewComparisonSourceProject.create(self.FIXTURE)
        self.addCleanup(self._source_project.cleanup)
        BundledReviewRulePolicyWriter(
            plugin_root=self.PROJECT_ROOT,
            project_root=self._source_project.root,
        ).write_only(self.WORKFLOW_ID)
        super().setUp()

    @property
    def execution_project_root(self) -> Path:
        return self._source_project.root

    @property
    def workflow_parameters(self) -> PrepareReviewInput:
        return PrepareReviewInput(
            target=FileAnalysisSource(
                path=self._source_project.review_target,
            )
        )

    @property
    def scenario(self) -> LiveWorkflowScenario:
        return LiveWorkflowScenario(
            workflow_id=self.REVIEW_WORKFLOW_ID,
            parameters=self.workflow_parameters,
            artifact_scope=LiveSessionArtifactScope(
                domain="review",
                scenario=self.ARTIFACT_SCENARIO,
            ),
            model_context=(
                "Source under review:\n"
                "```swift\n"
                f"{self._source_project.review_target.read_text(encoding='utf-8')}"
                "\n```"
            ),
        )

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        self._assert_codex_protocol(run)
        self.assert_rule_workflow(run, self._validation_expectation())

    def assert_rule_workflow(
        self,
        run: PreservedLiveWorkflowRun,
        expectation: LiveRuleValidationExpectation,
    ) -> None:
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        self.assertEqual(events[-1]["event"], "run_completed")
        self.assertFalse(
            {event.get("event") for event in events}
            & {"step_attempt_failed", "step_rejected", "run_failed"}
        )

        completed_steps = [
            event
            for event in events
            if event.get("event") == "step_completed"
            and self._belongs_to_rule(event.get("workflow_instance_id"))
            and event.get("workflow_source_index") == expectation.source_index
        ]
        completed_step_ids = {
            event["local_step_id"] for event in completed_steps
        }
        expected_step_ids = {
            *expectation.analysis_step_ids,
            *(metric.step_id for metric in expectation.metrics),
            "classify_exception",
        }
        if expectation.allow_auxiliary_steps:
            self.assertLessEqual(expected_step_ids, completed_step_ids)
        else:
            self.assertEqual(completed_step_ids, expected_step_ids)
        for metric in expectation.metrics:
            completed = next(
                event
                for event in completed_steps
                if event["local_step_id"] == metric.step_id
            )
            self.assertEqual(completed["outputs"]["value"], metric.value)
            self.assertTrue(completed["outputs"]["additional_info"]["reasoning"])
            self.assertTrue(completed["outputs"]["additional_info"]["evidence"])
        exception_step = next(
            event
            for event in completed_steps
            if event["local_step_id"] == "classify_exception"
        )
        self.assertEqual(
            exception_step["outputs"]["is_exception"],
            expectation.is_exception,
        )

        workflow_instance_ids = {
            event["workflow_instance_id"] for event in completed_steps
        }
        recorded_sessions = [
            event
            for event in events
            if event.get("event") == "session_step_recorded"
            and any(
                event["instance_id"].startswith(f"{workflow_instance_id}.")
                for workflow_instance_id in workflow_instance_ids
            )
        ]
        recorded_step_ids = {
            step_id
            for event in recorded_sessions
            for step_id in expected_step_ids
            if event["instance_id"].endswith(f".{step_id}-1")
        }
        if expectation.allow_auxiliary_steps:
            self.assertLessEqual(expected_step_ids, recorded_step_ids)
        else:
            self.assertEqual(recorded_step_ids, expected_step_ids)
            self.assertEqual(len(recorded_sessions), len(expected_step_ids))
        self._assert_review_result(run.run_directory, expectation)

    def _assert_review_result(
        self,
        run_directory: Path,
        expectation: LiveRuleValidationExpectation,
    ) -> None:
        review_directory = run_directory / "results" / "review"
        aggregate = ReviewResult.model_validate_json(
            (review_directory / "result.json").read_text()
        )
        self.assertEqual(aggregate.workflow_id, self.REVIEW_WORKFLOW_ID)
        self.assertEqual(aggregate.severity, expectation.final_severity)
        self.assertEqual(
            len(aggregate.rule_results),
            expectation.rule_result_count,
        )
        for aggregate_result in aggregate.rule_results:
            preserved_result = RuleReviewResult.model_validate_json(
                (
                    review_directory
                    / aggregate_result.workflow_id
                    / aggregate_result.rule_instance_id
                    / "result.json"
                ).read_text()
            )
            self.assertEqual(preserved_result, aggregate_result)

        matching_results = [
            result
            for result in aggregate.rule_results
            if result.workflow_id == expectation.workflow_id
            and result.provenance.source_index == expectation.source_index
        ]
        self.assertEqual(len(matching_results), 1)
        result = matching_results[0]
        self.assertEqual(result.workflow_id, expectation.workflow_id)
        self.assertEqual(result.severity, expectation.final_severity)
        self.assertEqual(result.scoring_authority, "mcp")
        self.assertEqual(result.exception.is_exception, expectation.is_exception)
        self.assertEqual(
            [metric.metric_id for metric in result.metrics],
            [metric.metric_id for metric in expectation.metrics],
        )
        self.assertEqual(
            [metric.observation_id for metric in result.metrics],
            [metric.observation_id for metric in expectation.metrics],
        )
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            [metric.severity for metric in expectation.metrics],
        )
        self.assertEqual(
            [metric.value for metric in result.metrics],
            [metric.value for metric in expectation.metrics],
        )

    def _belongs_to_rule(self, identity: object) -> bool:
        return (
            isinstance(identity, str)
            and f".rule_reviews.{self.WORKFLOW_ID}-" in identity
        )

    def _assert_codex_protocol(self, run: PreservedLiveWorkflowRun) -> None:
        if self.MODEL_PROFILE != "codex":
            return
        sessions = run.session.artifact_directory / "codex-runtime" / "sessions"
        transcripts = sorted(sessions.rglob("*.jsonl")) if sessions.exists() else []
        self.assertEqual(len(transcripts), 1, "Expected one preserved Codex transcript")
        evidence = CodexProtocolReader().read(transcripts[0])
        evidence_path = run.session.artifact_directory / "codex-protocol-evidence.json"
        evidence_path.write_text(evidence.model_dump_json(indent=2), encoding="utf-8")
        # Code mode may print content text without the MCP envelope. Do not
        # infer success from that text: require the same session's server ledger.
        server_confirmed = (
            self._has_completed_session_evidence(run)
            and not evidence.failed_calls
            and not evidence.unanswered_call_ids
        )
        print(
            f"Codex protocol: discovery={len(evidence.discovery_call_ids)}, "
            f"enveloped_start={len(evidence.successful_flow_start_call_ids)}/{evidence.flow_start_attempts}, "
            f"enveloped_next={len(evidence.successful_flow_next_call_ids)}/{evidence.flow_next_attempts}, "
            f"server_confirmed={server_confirmed}, "
            f"failed_calls={len(evidence.failed_calls)}, "
            f"unanswered_calls={len(evidence.unanswered_call_ids)}. Evidence: {evidence_path}"
        )
        self.assertTrue(
            evidence.successful_flow_start_call_ids or (server_confirmed and evidence.flow_start_attempts > 0),
            "Expected a successful flow_start MCP response",
        )
        self.assertTrue(
            evidence.successful_flow_next_call_ids or (server_confirmed and evidence.flow_next_attempts > 0),
            "Expected a successful flow_next MCP response",
        )
        self.assertFalse(evidence.unanswered_call_ids, "Tool calls have no recorded responses")
        source = self.FIXTURE.read_text(encoding="utf-8")
        self.assertEqual("\n".join(evidence.user_prompts).count(source), 1)
        self.assertNotIn(source, "\n".join(evidence.tool_outputs))
        self.assertNotIn(
            "Show the following output to the user exactly as-is",
            transcripts[0].read_text(encoding="utf-8"),
        )

    def _has_completed_session_evidence(self, run: PreservedLiveWorkflowRun) -> bool:
        events_path = run.run_directory / "events.jsonl"
        if not events_path.exists():
            return False
        events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
        sessions = {
            event.get("session_id") for event in events
            if event.get("event") == "session_step_recorded" and event.get("session_id") != "engine"
        }
        return bool(events) and (
            events[0].get("event") == "run_started"
            and events[-1].get("event") == "run_completed"
            and sessions == {run.session.session_id}
        )

    def _validation_expectation(self) -> LiveRuleValidationExpectation:
        self.assertEqual(len(self.EXPECTED_STEP_IDS), len(self.EXPECTED_METRIC_IDS))
        self.assertEqual(len(self.EXPECTED_STEP_IDS), len(self.EXPECTED_VALUES))
        self.assertEqual(
            len(self.EXPECTED_STEP_IDS),
            len(self.EXPECTED_METRIC_SEVERITIES),
        )
        if self.EXPECTED_OBSERVATION_IDS is not None:
            self.assertEqual(
                len(self.EXPECTED_STEP_IDS),
                len(self.EXPECTED_OBSERVATION_IDS),
            )
        return LiveRuleValidationExpectation(
            workflow_id=self.WORKFLOW_ID,
            analysis_step_ids=self.EXPECTED_ANALYSIS_STEP_IDS,
            metrics=[
                RuleMetricResultExpectation(
                    step_id=step_id,
                    metric_id=self.EXPECTED_METRIC_IDS[index],
                    observation_id=(
                        self.EXPECTED_OBSERVATION_IDS[index]
                        if self.EXPECTED_OBSERVATION_IDS is not None
                        else "value"
                    ),
                    value=self.EXPECTED_VALUES[index],
                    severity=self.EXPECTED_METRIC_SEVERITIES[index],
                )
                for index, step_id in enumerate(self.EXPECTED_STEP_IDS)
            ],
            final_severity=self.EXPECTED_FINAL_SEVERITY,
            is_exception=self.EXPECTED_EXCEPTION,
            allow_auxiliary_steps=self.ALLOW_AUXILIARY_STEPS,
            source_index=self.EXPECTED_RULE_SOURCE_INDEX,
            rule_result_count=self.EXPECTED_RULE_RESULT_COUNT,
        )
