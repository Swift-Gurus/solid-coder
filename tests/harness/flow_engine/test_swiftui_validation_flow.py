"""
solid-name: test_swiftui_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055, SPEC-057]
solid-description: Verifies SwiftUI applicability, canonical instructions, independently scored observations, exceptions, and audited results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestSwiftUIValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="swiftui",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "coding"
            / "apple"
            / "SwiftUI"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "coding"
            / "apple"
            / "swiftui"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_countable_observations",
                output={
                    "observations": [
                        {
                            "classification": "IMPURE_VIEW_MEMBER",
                            "location": "DashboardView.filteredRows",
                            "is_exception": False,
                            "reasoning": "The computed property filters domain data in the view.",
                            "evidence": "viewModel.rows.filter executes in filteredRows.",
                        },
                        {
                            "classification": "PREVIEW_ONLY_TYPE",
                            "location": "PreviewOnlyBadge",
                            "is_exception": False,
                            "reasoning": "The orphaned file-scope view has no production caller.",
                            "evidence": "Repository evidence contains no production reference.",
                        },
                        {
                            "classification": "VIEW_WITHOUT_PREVIEW",
                            "location": "DashboardView",
                            "is_exception": False,
                            "reasoning": "No preview instantiates DashboardView.",
                            "evidence": "Repository evidence contains no matching preview.",
                        },
                        {
                            "classification": "VIEW_WITHOUT_PREVIEW",
                            "location": "PreviewOnlyBadge",
                            "is_exception": False,
                            "reasoning": "No preview instantiates PreviewOnlyBadge.",
                            "evidence": "Repository evidence contains no matching preview.",
                        },
                        {
                            "classification": "BAD_CONTAINER_ACCESSIBILITY",
                            "location": "DashboardView.body.HStack",
                            "is_exception": False,
                            "reasoning": "The container identifier lacks accessibilityElement.",
                            "evidence": "HStack applies accessibilityIdentifier directly.",
                        },
                        {
                            "classification": "FIXED_FRAME",
                            "location": "DashboardView.body.TextField",
                            "is_exception": False,
                            "reasoning": "The child uses literal width and height values.",
                            "evidence": ".frame(width: 240, height: 44)",
                        },
                        {
                            "classification": "OVER_ISOLATED",
                            "location": "DashboardViewModel",
                            "is_exception": False,
                            "reasoning": "The globally isolated model contains background-safe work.",
                            "evidence": "@MainActor type contains fetchRows().",
                        },
                    ],
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_extrema_observations",
                output={
                    "view_properties": [
                        {
                            "location": "DashboardView.body",
                            "nesting_depth": 3,
                            "expression_count": 8,
                            "is_exception": False,
                            "reasoning": "The body contains the deepest builder tree.",
                            "evidence": "VStack > List > HStack in body.",
                        },
                        {
                            "location": "DashboardView.emptyState",
                            "nesting_depth": 1,
                            "expression_count": 2,
                            "is_exception": False,
                            "reasoning": "The helper contains one shallow container.",
                            "evidence": "VStack with Text in emptyState.",
                        },
                    ],
                    "modifier_chains": [
                        {
                            "location": "DashboardView.body.TextField",
                            "length": 2,
                            "is_exception": False,
                            "reasoning": "The nested child has two modifiers.",
                            "evidence": "TextField applies textFieldStyle and frame.",
                        },
                        {
                            "location": "DashboardView.body.HStack",
                            "length": 2,
                            "is_exception": False,
                            "reasoning": "A second child has the same maximum.",
                            "evidence": "HStack applies accessibility modifiers.",
                        },
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(step_id="body_nesting_depth", metric_id="SUI-1", observation_id="body_nesting_depth", detection_id="SUI-1", detection_name="Body Complexity", value=3, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="view_expression_count", metric_id="SUI-1", observation_id="view_expression_count", detection_id="SUI-1", detection_name="Body Complexity", value=8, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="impure_count", metric_id="SUI-2", detection_id="SUI-2", detection_name="View Purity", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="max_modifier_chain", metric_id="SUI-3", detection_id="SUI-3", detection_name="Modifier Chain Length", value=2, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="vm_injection_style", metric_id="SUI-4", detection_id="SUI-4", detection_name="ViewModel Injection", value="concrete", severity="SEVERE"),
            RuleMetricExpectation(step_id="preview_only_count", metric_id="SUI-5", detection_id="SUI-5", detection_name="Preview-Only View Containment", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="views_without_preview_count", metric_id="SUI-6", detection_id="SUI-6", detection_name="Preview Coverage", value=2, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="bad_accessibility_count", metric_id="SUI-7", detection_id="SUI-7", detection_name="Accessibility Identifier on Containers", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="fixed_frame_count", metric_id="SUI-8", detection_id="SUI-8", detection_name="Adaptive Sizing", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="over_isolated_count", metric_id="SUI-9", detection_id="SUI-9", detection_name="Actor Isolation Granularity", value=1, severity="SEVERE", mcp_owned=True),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_unit_kinds=["struct"],
        included_tags=["swiftui", "view"],
    )

    def test_observation_exception_excludes_only_matching_metric(self) -> None:
        started = self._start()
        observations = [
            {
                **observation,
                "is_exception": observation["classification"] == "FIXED_FRAME",
            }
            for observation in self.SCENARIO.analysis[0].output["observations"]
        ]

        countable = next(
            step
            for step in started.steps
            if step.step_id == "classify_countable_observations"
        )
        extrema = next(
            step
            for step in started.steps
            if step.step_id == "classify_extrema_observations"
        )
        ready = self.sut.flow_next({
            countable.instance_id: {"observations": observations},
            extrema.instance_id: self.SCENARIO.analysis[1].output,
        })
        completed = self._finish_ready_workflow(ready, started.run_id)

        self.assertEqual(completed.result.status, "done", completed.result.error)
        result = self._rule_result(started.run_id)
        metrics = {
            (metric.metric_id, metric.observation_id): metric
            for metric in result.metrics
        }
        fixed_frame = metrics[("SUI-8", "value")]
        self.assertEqual(fixed_frame.value, 0)
        self.assertEqual(fixed_frame.severity, "COMPLIANT")
        self.assertEqual(metrics[("SUI-7", "value")].value, 1)
        self.assertEqual(result.severity, "SEVERE")

    def test_extrema_preserve_equal_maximum_observations(self) -> None:
        checkpoint = self._advance_through_analysis()
        modifier_event = next(
            event
            for event in self._events(checkpoint.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "max_modifier_chain"
        )

        self.assertEqual(modifier_event["outputs"]["value"], 2)
        self.assertEqual(
            modifier_event["metric_derivation"]["projection_evidence"],
            [
                {"index": 0, "value": 2},
                {"index": 1, "value": 2},
            ],
        )

    def test_empty_extrema_collections_use_authored_zero_values(self) -> None:
        started = self._start()
        countable = next(
            step
            for step in started.steps
            if step.step_id == "classify_countable_observations"
        )
        extrema = next(
            step
            for step in started.steps
            if step.step_id == "classify_extrema_observations"
        )
        ready = self.sut.flow_next({
            countable.instance_id: self.SCENARIO.analysis[0].output,
            extrema.instance_id: {
                "view_properties": [],
                "modifier_chains": [],
            },
        })
        self._finish_ready_workflow(ready, started.run_id)
        metrics = {
            (metric.metric_id, metric.observation_id): metric.value
            for metric in self._rule_result(started.run_id).metrics
        }

        self.assertEqual(metrics[("SUI-1", "body_nesting_depth")], 0)
        self.assertEqual(metrics[("SUI-1", "view_expression_count")], 0)
        self.assertEqual(metrics[("SUI-3", "value")], 0)

    def test_rejects_an_observation_without_required_evidence(self) -> None:
        started = self._start()
        invalid = dict(self.SCENARIO.analysis[0].output["observations"][0])
        invalid.pop("evidence")

        classifier = next(
            step
            for step in started.steps
            if step.step_id == "classify_countable_observations"
        )
        rejected = self.sut.flow_next({
            classifier.instance_id: {"observations": [invalid]},
        })

        self.assertEqual(rejected.status, "ready")
        step_ids = {step.step_id for step in rejected.steps}
        self.assertIn("classify_countable_observations", step_ids)
        self.assertTrue(
            {
                "impure_count",
                "preview_only_count",
                "views_without_preview_count",
                "bad_accessibility_count",
                "fixed_frame_count",
                "over_isolated_count",
            }.isdisjoint(step_ids)
        )
        classifier = next(
            step
            for step in rejected.steps
            if step.step_id == "classify_countable_observations"
        )
        self.assertIn("evidence", classifier.rejection_reason)

    def _events(self, run_id: str) -> list[dict[str, object]]:
        events_path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
