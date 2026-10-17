"""Validates the bundled ISP rule through the shared deterministic rule contract."""

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.rule_applicability_context import RuleApplicabilityContext
from isp_rule_workflow_parameters import ISPRuleWorkflowParameters
from review.normalized_review_unit import NormalizedReviewUnit
from rule_analysis_expectation import RuleAnalysisExpectation
from rule_metric_expectation import RuleMetricExpectation
from rule_validation_flow_contract import RuleValidationFlowContract
from rule_validation_scenario import RuleValidationScenario
from rule_workflow_checkpoint import RuleWorkflowCheckpoint
from source.file_analysis_source import FileAnalysisSource
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import PrepareSearchTargetsOperationFactory
from source.search_target_granularity import SearchTargetGranularity
from source.source_search_context import SourceSearchContext


"""
solid-name: TestISPValidationFlow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-057]
solid-description: Verifies the real bundled ISP rule scores exposed definition and extension members with engine-owned width, distinct responsibilities and stakeholders.
"""
class TestISPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="isp",
        rule_path=_PROJECT_ROOT / "references/principles/ISP/rule.md",
        fixture_path=_PROJECT_ROOT / "tests/principles/ISP/fixtures/fixture-1.swift",
        analysis=[
            RuleAnalysisExpectation(step_id="classify_members", output={}),
        ],
        metrics=[
            RuleMetricExpectation(step_id="width", metric_id="ISP-1", detection_id="ISP-1", detection_name="Protocol Width", value=10, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="responsibilities", metric_id="ISP-3", detection_id="ISP-3", detection_name="Independent Responsibilities", value=2, severity="COMPLIANT", mcp_owned=True),
            RuleMetricExpectation(step_id="stakeholders", metric_id="ISP-5", detection_id="ISP-5", detection_name="Stakeholders", value=1, severity="COMPLIANT", mcp_owned=True),
        ],
        final_severity="SEVERE",
        included_unit_kinds=["protocol", "extension"],
    )

    def setUp(self) -> None:
        super().setUp()
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(source=FileAnalysisSource(path=self.SCENARIO.fixture_path), granularity=SearchTargetGranularity.UNIT),
        )
        protocol = next(target for target in prepared.targets if target.kind == "protocol")
        self.review_unit = "protocol DocumentService {"
        self.review_unit_name = protocol.name
        self._parameters = ISPRuleWorkflowParameters(
            review_unit=NormalizedReviewUnit(
                target=protocol,
                applicability=RuleApplicabilityContext(file_extension=".swift", unit_kind="protocol", tags=[]),
                tag_evidence=[],
            ),
            source_context=SourceSearchContext(sources=[prepared.snapshot]),
        )

    def _start(self):
        return self.sut.flow_start("isp", self._parameters.model_dump(mode="json"))

    def _advance_through_analysis(self) -> RuleWorkflowCheckpoint:
        current = self._start()
        self.assertIsNone(current.error, current.error)
        run_id = current.run_id
        prompts = []
        step_ids = []
        while current.steps and not all(step.step_id == "classify_exception" for step in current.steps):
            prompts.extend(step.prompt for step in current.steps)
            step_ids.extend(step.step_id for step in current.steps)
            submissions = {}
            for index, step in enumerate(current.steps):
                self.assertEqual(step.step_id, "classify_members")
                submissions[step.batch.label] = {
                    "assessment": {
                        "verification": "VERIFIED",
                        "action": "read" if index < 5 else "write",
                        "responsibility": "reading" if index < 5 else "writing",
                        "stakeholder": "document users",
                        "is_exception": False,
                        "additional_info": {
                            "reasoning": "This declaration serves document reading or writing.",
                            "evidence": step.batch.label,
                        },
                    },
                }
            current = self.sut.flow_next(submissions)
            self.assertIsNone(current.error, current.error)
        self.assertEqual([step.step_id for step in current.steps], ["classify_exception"])
        prompts.extend(step.prompt for step in current.steps)
        step_ids.extend(step.step_id for step in current.steps)
        return RuleWorkflowCheckpoint(run_id=run_id, result=current, prompts=prompts, step_ids=step_ids)

    def test_repository_evidence_is_reduced_without_model_owned_metrics(self) -> None:
        checkpoint = self._advance_through_analysis()
        events = self._events(checkpoint.run_id)
        completed = [event for event in events if event.get("event") == "step_completed"]
        self.assertEqual([event["step_id"] for event in completed].count("discover"), 1)
        self.assertEqual([event["step_id"] for event in completed].count("prepare_context"), 1)
        self.assertFalse(any(event["step_id"].endswith(".match") for event in completed))
        self.assertEqual(
            {event["step_id"]: event["outputs"]["value"] for event in completed
             if event["step_id"] in {metric.step_id for metric in self.SCENARIO.metrics}},
            {"width": 10, "responsibilities": 2, "stakeholders": 1},
        )
        self.assertIn("func open", " ".join(checkpoint.prompts))

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._complete_workflow()
        prompts = " ".join(" ".join(checkpoint.prompts).split())
        for classification in ["action", "responsibility", "stakeholder", "is_exception", "UNABLE_TO_VERIFY"]:
            self.assertIn(classification, prompts)
        for exception in ["marker protocols", "composition protocols", "@objc", "test code"]:
            self.assertIn(exception, prompts.lower())
        self.assertIn("Default implementations do not exempt additional exposed behavior.", prompts)
        self.assertNotIn("usage_vector", prompts)
        self.assertNotIn("coverage_entries", prompts)
        self.assertNotIn("Calculate coverage", prompts)
        self.assertEqual(self._rule_result(checkpoint.run_id).unavailable_metrics, [])

    def _events(self, run_id: str) -> list[dict]:
        return [json.loads(line) for line in (self.project_root / "runs" / run_id / "events.jsonl").read_text().splitlines()]
