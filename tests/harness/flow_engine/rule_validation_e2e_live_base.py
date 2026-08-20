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
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_workflow_e2e_live_base import LiveWorkflowE2ELiveBase  # noqa: E402
from live_workflow_scenario import LiveWorkflowScenario  # noqa: E402
from preserved_live_workflow_run import PreservedLiveWorkflowRun  # noqa: E402
from review_unit_workflow_parameters import ReviewUnitWorkflowParameters  # noqa: E402


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
    EXPECTED_METRIC_IDS: ClassVar[list[str]]
    EXPECTED_VALUES: ClassVar[list[int | float | str | bool]]
    EXPECTED_METRIC_SEVERITIES: ClassVar[list[str]]
    EXPECTED_FINAL_SEVERITY: ClassVar[str]
    EXPECTED_EXCEPTION: ClassVar[bool] = False

    @property
    def scenario(self) -> LiveWorkflowScenario:
        return LiveWorkflowScenario(
            workflow_id=self.WORKFLOW_ID,
            parameters=ReviewUnitWorkflowParameters(
                review_unit=self.FIXTURE.read_text(encoding="utf-8"),
            ),
            artifact_scope=LiveSessionArtifactScope(
                domain="review",
                scenario=self.ARTIFACT_SCENARIO,
            ),
        )

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
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
            event for event in events if event.get("event") == "step_completed"
        ]
        self.assertEqual(
            {event["step_id"] for event in completed_steps},
            {*self.EXPECTED_STEP_IDS, "classify_exception"},
        )
        for step_id, expected_value in zip(
            self.EXPECTED_STEP_IDS,
            self.EXPECTED_VALUES,
        ):
            completed = next(
                event for event in completed_steps if event["step_id"] == step_id
            )
            self.assertEqual(completed["outputs"]["value"], expected_value)
            self.assertTrue(completed["outputs"]["additional_info"]["reasoning"])
            self.assertTrue(completed["outputs"]["additional_info"]["evidence"])
        exception_step = next(
            event
            for event in completed_steps
            if event["step_id"] == "classify_exception"
        )
        self.assertEqual(
            exception_step["outputs"]["is_exception"],
            self.EXPECTED_EXCEPTION,
        )

        recorded_sessions = [
            event for event in events if event.get("event") == "session_step_recorded"
        ]
        self.assertEqual(
            {event["instance_id"] for event in recorded_sessions},
            {
                *(f"{step_id}-1" for step_id in self.EXPECTED_STEP_IDS),
                "classify_exception-1",
            },
        )
        self._assert_review_result(run.run_directory)

    def _assert_review_result(self, run_directory: Path) -> None:
        review_directory = run_directory / "results" / "review"
        aggregate = ReviewResult.model_validate_json(
            (review_directory / "result.json").read_text()
        )
        self.assertEqual(aggregate.workflow_id, self.WORKFLOW_ID)
        self.assertEqual(aggregate.severity, self.EXPECTED_FINAL_SEVERITY)
        self.assertEqual(len(aggregate.rule_results), 1)

        result = aggregate.rule_results[0]
        preserved_rule_result = RuleReviewResult.model_validate_json(
            (
                review_directory
                / result.workflow_id
                / result.rule_instance_id
                / "result.json"
            ).read_text()
        )
        self.assertEqual(preserved_rule_result, result)
        self.assertEqual(result.workflow_id, self.WORKFLOW_ID)
        self.assertEqual(result.severity, self.EXPECTED_FINAL_SEVERITY)
        self.assertEqual(result.scoring_authority, "mcp")
        self.assertEqual(result.exception.is_exception, self.EXPECTED_EXCEPTION)
        self.assertEqual(
            [metric.metric_id for metric in result.metrics],
            self.EXPECTED_METRIC_IDS,
        )
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            self.EXPECTED_METRIC_SEVERITIES,
        )
        self.assertEqual(
            [metric.value for metric in result.metrics],
            self.EXPECTED_VALUES,
        )
