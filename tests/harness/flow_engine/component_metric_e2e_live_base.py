"""Shares the live component-count contract across model backends."""

import json
import sys
import tempfile
from pathlib import Path
from typing import ClassVar

from pydantic import RootModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.review_result import ReviewResult
from harness.rule_review_result import RuleReviewResult
from live_session_artifact_scope import LiveSessionArtifactScope
from live_workflow_e2e_live_base import LiveWorkflowE2ELiveBase
from live_workflow_scenario import LiveWorkflowScenario
from preserved_live_workflow_run import PreservedLiveWorkflowRun

"""
solid-name: ComponentMetricE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-059]
solid-description: Uses the shared live-session harness to verify model classification leads to engine-owned component scoring and durable audit.
"""


class ComponentMetricE2ELiveBase(LiveWorkflowE2ELiveBase):
    __test__ = False
    PROJECT_ROOT: ClassVar[Path] = Path(__file__).resolve().parents[3]

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="component-metric-live-")
        self.addCleanup(temporary.cleanup)
        self.project_directory = Path(temporary.name)
        super().setUp()

    @property
    def execution_project_root(self) -> Path:
        return self.project_directory

    @property
    def scenario(self) -> LiveWorkflowScenario:
        return LiveWorkflowScenario(
            workflow_id=str(
                Path(__file__).parent / "fixtures/component_count/workflow.yaml"
            ),
            parameters=RootModel[dict[str, object]]({}),
            artifact_scope=LiveSessionArtifactScope(
                domain="flow-engine", scenario="component-count"
            ),
        )

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        print(
            f"\nComponent metric live artifacts: {run.session.artifact_directory}\n",
            flush=True,
        )
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
        ]
        completed = [event for event in events if event["event"] == "step_completed"]
        self.assertEqual(
            [event["step_id"] for event in completed],
            ["classify", "groups", "classify_exception"],
        )
        metric = completed[1]
        self.assertEqual(metric["session_id"], "engine")
        self.assertEqual(metric["outputs"]["value"], 2)
        self.assertEqual(metric["metric_derivation"]["excluded_indexes"], [4])
        self.assertEqual(
            metric["metric_derivation"]["component_evidence"]["components"],
            [[0, 1, 2], [3]],
        )
        self.assertEqual(sum(event["session_id"] != "engine" for event in completed), 2)
        self.assertFalse(
            {"step_attempt_failed", "step_rejected", "run_failed"}.intersection(
                event["event"] for event in events
            )
        )
        self.assertEqual(events[-1]["event"], "run_completed")
        review_directory = run.run_directory / "results/review"
        aggregate = ReviewResult.model_validate_json(
            (review_directory / "result.json").read_text()
        )
        self.assertEqual(aggregate.workflow_id, "component-count-contract")
        self.assertEqual(aggregate.severity, "SEVERE")
        self.assertEqual(len(aggregate.rule_results), 1)
        result = aggregate.rule_results[0]
        preserved = RuleReviewResult.model_validate_json(
            (
                review_directory
                / result.workflow_id
                / result.rule_instance_id
                / "result.json"
            ).read_text()
        )
        self.assertEqual(preserved, result)
        self.assertEqual(result.severity, "SEVERE")
        self.assertEqual(result.metrics[0].value, 2)
        self.assertEqual(
            result.metrics[0].derivation.component_evidence.model_dump(mode="json"),
            metric["metric_derivation"]["component_evidence"],
        )
