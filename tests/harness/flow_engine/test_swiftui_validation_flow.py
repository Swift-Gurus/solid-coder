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

from bundled_review_rule_policy_writer import BundledReviewRulePolicyWriter
from harness.sibling_batch_step_selector_factory import SiblingBatchStepSelectorFactory
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from review.review_operation_registrations_factory import (
    ReviewOperationRegistrationsFactory,
)
from rule_analysis_expectation import RuleAnalysisExpectation
from rule_metric_expectation import RuleMetricExpectation
from rule_validation_flow_contract import RuleValidationFlowContract
from rule_validation_scenario import RuleValidationScenario


class TestSwiftUIValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="swiftui",
        rule_path=(
            _PROJECT_ROOT / "references" / "coding" / "apple" / "SwiftUI" / "rule.md"
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
                    "preview_limitations": [],
                    "preview_facts": [
                        {
                            "is_preview": False,
                            "is_file_scope": True,
                            "has_preview": False,
                            "reasoning": "The reviewed production view has no preview in the supplied source.",
                            "evidence": "DashboardView is declared at file scope; the file has no #Preview or PreviewProvider.",
                        }
                    ],
                    "observations": [
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
                    "limitations": [],
                    "view_properties": [
                        {
                            "location": "DashboardView.body",
                            "deepest_path": ["VStack", "HStack"],
                            "expressions": [
                                "VStack",
                                "HStack",
                                "Text",
                                "Image",
                                "Button",
                                "TextField",
                                "Text",
                                "Divider",
                            ],
                            "is_preview": False,
                            "is_app_entry_point": False,
                            "reasoning": "The body contains the deepest builder tree.",
                            "evidence": "VStack > HStack in body.",
                        },
                        {
                            "location": "DashboardView.emptyState",
                            "deepest_path": ["VStack"],
                            "expressions": ["VStack", "Text"],
                            "is_preview": False,
                            "is_app_entry_point": False,
                            "reasoning": "The helper contains one shallow container.",
                            "evidence": "VStack with Text in emptyState.",
                        },
                    ],
                    "modifier_chains": [
                        {
                            "location": "DashboardView.body.TextField",
                            "modifiers": ["textFieldStyle", "frame"],
                            "is_preview": False,
                            "is_nested_child": True,
                            "reasoning": "The nested child has two modifiers.",
                            "evidence": "TextField applies textFieldStyle and frame.",
                        },
                        {
                            "location": "DashboardView.body.HStack",
                            "modifiers": [
                                "accessibilityElement",
                                "accessibilityIdentifier",
                            ],
                            "is_preview": False,
                            "is_nested_child": True,
                            "reasoning": "A second child has the same maximum.",
                            "evidence": "HStack applies accessibility modifiers.",
                        },
                    ],
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_view_purity",
                output={
                    "limitations": [],
                    "behaviors": [
                        {
                            "classification": "TRANSFORM",
                            "location": "DashboardView.filteredRows",
                            "is_preview": False,
                            "reasoning": "The property filters domain data.",
                            "evidence": "viewModel.rows.filter { query.isEmpty || $0.contains(query) }",
                        },
                        {
                            "classification": "FORMAT",
                            "location": "DashboardView.body",
                            "is_preview": False,
                            "reasoning": "The body builds a formatted string outside SwiftUI formatting.",
                            "evidence": 'Text(filteredRows.joined(separator: ", "))',
                        },
                        {
                            "classification": "ACTION_FORWARDING",
                            "location": "DashboardView.body.Button.Task",
                            "is_preview": False,
                            "reasoning": "The closure only forwards the action.",
                            "evidence": "try? await viewModel.load()",
                        },
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="body_nesting_depth",
                metric_id="SUI-1",
                detection_id="SUI-1",
                detection_name="Builder Nesting Depth",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="view_expression_count",
                metric_id="SUI-2",
                detection_id="SUI-2",
                detection_name="View Expression Count",
                value=8,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="max_modifier_chain",
                metric_id="SUI-3",
                detection_id="SUI-3",
                detection_name="Modifier Chain Length",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="impure_count",
                metric_id="SUI-4",
                detection_id="SUI-4",
                detection_name="View Purity",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="vm_injection_style",
                metric_id="SUI-5",
                detection_id="SUI-5",
                detection_name="ViewModel Injection",
                value="concrete",
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="preview_only_count",
                metric_id="SUI-6",
                detection_id="SUI-6",
                detection_name="Preview-Only View Containment",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="views_without_preview_count",
                metric_id="SUI-7",
                detection_id="SUI-7",
                detection_name="Preview Coverage",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="bad_accessibility_count",
                metric_id="SUI-8",
                detection_id="SUI-8",
                detection_name="Accessibility Identifier on Containers",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="fixed_frame_count",
                metric_id="SUI-9",
                detection_id="SUI-9",
                detection_name="Adaptive Sizing",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="over_isolated_count",
                metric_id="SUI-10",
                detection_id="SUI-10",
                detection_name="Actor Isolation Granularity",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_unit_kinds=["struct"],
        included_tags=["swiftui", "view"],
    )

    def setUp(self) -> None:
        self.SCENARIO = self.SCENARIO.model_copy(deep=True)
        super().setUp()

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._complete_workflow()
        prompts = "\n".join(checkpoint.prompts)

        for required in [
            "builder-only",
            "expression occurrences",
            "named subview",
            "No demonstrated reuse",
            "including `body`",
            "Button actions",
            "innermost owning",
            "action forwarding",
            "SwiftUI-native",
            "Task lifecycle",
            "limitations",
            "only the relevant observation",
            "`is_preview`",
            "`has_preview`",
            "reviewed view only",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, prompts)

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
        ready = self.sut.flow_next(
            {
                countable.instance_id: {
                    **self.SCENARIO.analysis[0].output,
                    "observations": observations,
                },
                extrema.instance_id: self.SCENARIO.analysis[1].output,
                next(
                    step.instance_id
                    for step in started.steps
                    if step.step_id == "classify_view_purity"
                ): self.SCENARIO.analysis[2].output,
            }
        )
        completed = self._finish_ready_workflow(ready, started.run_id)

        self.assertEqual(completed.result.status, "done", completed.result.error)
        result = self._rule_result(started.run_id)
        metrics = {
            (metric.metric_id, metric.observation_id): metric
            for metric in result.metrics
        }
        fixed_frame = metrics[("SUI-9", "value")]
        self.assertEqual(fixed_frame.value, 0)
        self.assertEqual(fixed_frame.severity, "COMPLIANT")
        self.assertEqual(metrics[("SUI-8", "value")].value, 1)
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
        ready = self.sut.flow_next(
            {
                countable.instance_id: self.SCENARIO.analysis[0].output,
                extrema.instance_id: {
                    "limitations": [],
                    "view_properties": [],
                    "modifier_chains": [],
                },
                next(
                    step.instance_id
                    for step in started.steps
                    if step.step_id == "classify_view_purity"
                ): self.SCENARIO.analysis[2].output,
            }
        )
        self._finish_ready_workflow(ready, started.run_id)
        metrics = {
            (metric.metric_id, metric.observation_id): metric.value
            for metric in self._rule_result(started.run_id).metrics
        }

        self.assertEqual(metrics[("SUI-1", "value")], 0)
        self.assertEqual(metrics[("SUI-2", "value")], 0)
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
        rejected = self.sut.flow_next(
            {
                classifier.instance_id: {
                    **self.SCENARIO.analysis[0].output,
                    "observations": [invalid],
                },
            }
        )

        self.assertEqual(rejected.status, "ready")
        step_ids = {step.step_id for step in rejected.steps}
        self.assertIn("classify_countable_observations", step_ids)
        self.assertTrue(
            {
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

    def test_app_entry_exempts_depth_but_not_size_or_impurity(self) -> None:
        self.SCENARIO.analysis[1].output["view_properties"][0]["is_app_entry_point"] = (
            True
        )

        completed = self._complete_workflow()
        metrics = self._rule_result(completed.run_id).metrics

        self.assertEqual([metric.value for metric in metrics[:4]], [1, 8, 2, 2])

    def test_root_modifier_chain_is_excluded_but_nested_chain_is_scored(self) -> None:
        chains = self.SCENARIO.analysis[1].output["modifier_chains"]
        chains[0]["is_nested_child"] = False
        chains[0]["modifiers"] = ["padding", "font", "background", "frame"]

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[2].value, 2)

    def test_preview_structure_is_excluded_without_hiding_production_members(
        self,
    ) -> None:
        self.SCENARIO.analysis[1].output["view_properties"][0]["is_preview"] = True

        completed = self._complete_workflow()

        self.assertEqual(
            [
                metric.value
                for metric in self._rule_result(completed.run_id).metrics[:2]
            ],
            [1, 2],
        )

    def test_multiple_impure_behaviors_in_one_scope_count_once(self) -> None:
        behaviors = self.SCENARIO.analysis[2].output["behaviors"]
        behaviors.append(
            {
                **behaviors[0],
                "classification": "COMPUTE",
                "reasoning": "The same property also computes derived state.",
            }
        )

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[3].value, 2)

    def test_body_button_task_and_lifecycle_business_logic_are_in_scope(self) -> None:
        self.SCENARIO.analysis[2].output["behaviors"] = [
            {
                "classification": classification,
                "location": location,
                "is_preview": False,
                "reasoning": "Business logic executes directly in this view scope.",
                "evidence": evidence,
            }
            for classification, location, evidence in [
                ("TRANSFORM", "body", "Text(rows.filter { $0.active }.description)"),
                ("VALIDATE", "body.Button.action", "if query.count > 3 { save() }"),
                ("DATA_FETCH", "body.task", "await repository.fetch()"),
                ("COMPUTE", "body.onAppear", "total = price * quantity"),
            ]
        ]

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[3].value, 4)

    def test_forwarding_native_formatting_and_view_composition_are_pure(self) -> None:
        self.SCENARIO.analysis[2].output["behaviors"] = [
            {
                "classification": classification,
                "location": location,
                "is_preview": False,
                "reasoning": "The scope only declares UI or forwards an action.",
                "evidence": evidence,
            }
            for classification, location, evidence in [
                (
                    "ACTION_FORWARDING",
                    "body.Button.Task",
                    "Task { await viewModel.load() }",
                ),
                (
                    "NATIVE_FORMAT",
                    "body.Text",
                    'Text(price, format: .currency(code: "USD"))',
                ),
                ("VIEW_COMPOSITION", "body", "ForEach(rows) { RowView(row: $0) }"),
                ("PRESENTATION_STATE", "body.Button.action", "isExpanded.toggle()"),
                ("APPEARANCE", "badge", "Text(label).font(.headline)"),
            ]
        ]

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[3].value, 0)

    def test_incomplete_structure_is_unavailable_not_zero(self) -> None:
        self.SCENARIO.analysis[1].output["limitations"] = [
            "Custom builder declaration is unavailable."
        ]

        completed = self._complete_workflow()
        result = self._rule_result(completed.run_id)

        self.assertEqual(
            [metric.metric_id for metric in result.unavailable_metrics],
            ["SUI-1", "SUI-2", "SUI-3"],
        )
        self.assertNotIn("SUI-1", [metric.metric_id for metric in result.metrics])

    def test_incomplete_purity_is_unavailable_not_zero(self) -> None:
        self.SCENARIO.analysis[2].output["limitations"] = [
            "A helper implementation is missing."
        ]

        completed = self._complete_workflow()

        self.assertEqual(
            [
                metric.metric_id
                for metric in self._rule_result(completed.run_id).unavailable_metrics
            ],
            ["SUI-4"],
        )

    def test_purity_rejects_missing_evidence_before_scoring(self) -> None:
        started = self._start()
        output = self.SCENARIO.analysis[2].output
        del output["behaviors"][0]["evidence"]
        classifier = next(
            step for step in started.steps if step.step_id == "classify_view_purity"
        )

        rejected = self.sut.flow_next({classifier.instance_id: output})

        self.assertIn(
            "evidence",
            next(
                step.rejection_reason
                for step in rejected.steps
                if step.step_id == "classify_view_purity"
            ),
        )

    def test_structure_below_all_three_thresholds_is_compliant(self) -> None:
        structure = self.SCENARIO.analysis[1].output
        structure["view_properties"][0]["deepest_path"] = ["VStack"]
        structure["view_properties"][0]["expressions"] = [
            "VStack",
            "Text",
            "Image",
            "Button",
        ]
        structure["modifier_chains"][0]["modifiers"] = ["padding"]
        structure["modifier_chains"][1]["modifiers"] = ["accessibilityIdentifier"]

        completed = self._complete_workflow()
        metrics = self._rule_result(completed.run_id).metrics[:3]

        self.assertEqual([metric.value for metric in metrics], [1, 4, 1])
        self.assertEqual([metric.severity for metric in metrics], ["COMPLIANT"] * 3)

    def test_preview_impurity_does_not_hide_production_impurity(self) -> None:
        self.SCENARIO.analysis[2].output["behaviors"][0]["is_preview"] = True

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[3].value, 1)

    def test_production_view_with_preview_remains_subject_to_purity(self) -> None:
        self.SCENARIO.analysis[0].output["preview_facts"][0]["has_preview"] = True

        completed = self._complete_workflow()
        metrics = self._rule_result(completed.run_id).metrics

        self.assertEqual([metric.value for metric in metrics[5:7]], [0, 0])
        self.assertEqual(metrics[3].severity, "SEVERE")

    def test_preview_only_file_scope_view_fails_containment_not_coverage(self) -> None:
        self.SCENARIO.analysis[0].output["preview_facts"][0]["is_preview"] = True

        completed = self._complete_workflow()

        self.assertEqual(
            [
                metric.value
                for metric in self._rule_result(completed.run_id).metrics[5:7]
            ],
            [1, 0],
        )

    def test_preview_only_nested_view_passes_containment_and_coverage(self) -> None:
        preview = self.SCENARIO.analysis[0].output["preview_facts"][0]
        preview["is_preview"] = True
        preview["is_file_scope"] = False

        completed = self._complete_workflow()

        self.assertEqual(
            [
                metric.value
                for metric in self._rule_result(completed.run_id).metrics[5:7]
            ],
            [0, 0],
        )

    def test_unresolved_preview_facts_are_unavailable_not_compliant(self) -> None:
        self.SCENARIO.analysis[0].output["preview_limitations"] = [
            "Preview source is incomplete."
        ]

        completed = self._complete_workflow()

        self.assertEqual(
            [
                metric.metric_id
                for metric in self._rule_result(completed.run_id).unavailable_metrics
            ],
            ["SUI-6", "SUI-7"],
        )

    def test_preview_schema_requires_both_flags_and_exactly_one_reviewed_view(
        self,
    ) -> None:
        valid = self.SCENARIO.analysis[0].output["preview_facts"][0]

        for invalid in [
            [],
            [valid, valid],
            [{key: value for key, value in valid.items() if key != "is_preview"}],
            [{key: value for key, value in valid.items() if key != "has_preview"}],
            [{key: value for key, value in valid.items() if key != "evidence"}],
        ]:
            with self.subTest(preview_facts=invalid):
                started = self.sut.flow_start(
                    "swiftui",
                    {"review_unit": {"target": {"name": "DashboardView"}}},
                    isolated=True,
                )
                classifier = next(
                    step
                    for step in started.steps
                    if step.step_id == "classify_countable_observations"
                )
                rejected = self.sut.flow_next(
                    {
                        classifier.instance_id: {
                            **self.SCENARIO.analysis[0].output,
                            "preview_facts": invalid,
                        },
                    },
                    run_id=started.run_id,
                )
                self.assertTrue(
                    next(
                        step.rejection_reason
                        for step in rejected.steps
                        if step.step_id == "classify_countable_observations"
                    )
                )

    def test_aggregate_submission_runs_counts_and_scores_every_metric(self) -> None:
        BundledReviewRulePolicyWriter(
            plugin_root=self.PROJECT_ROOT,
            project_root=self.project_root,
        ).write_only("swiftui")
        driver = OperationWorkflowIntegrationDriver(
            project_root=self.project_root,
            plugin_root=self.PROJECT_ROOT,
            registrations=ReviewOperationRegistrationsFactory().make(),
        )
        driver.workflow_path = (
            self.PROJECT_ROOT
            / "workflows/review/bundles/solid-file-review-aggregate/workflow.yaml"
        )
        started = driver.start(
            {
                "target": {
                    "kind": "text",
                    "text": self.review_unit,
                    "virtual_path": str(self.project_root / "Dashboard.swift"),
                },
                "context_sources": [],
            }
        )
        self.assertIsNone(started.error, started.error)
        selector = SiblingBatchStepSelectorFactory().make()

        ready = driver.advance(
            {
                step.batch.label: {
                    step.batch.workflow_alias: {
                        item.step_id: item.output for item in self.SCENARIO.analysis
                    }
                }
                for step in selector.select(started.steps[0], started.steps)
            }
        )
        self.assertIsNone(ready.error, ready.error)
        completed = driver.advance(
            {
                step.batch.label: {
                    step.batch.workflow_alias: {
                        "vm_injection_style": self._output_for("vm_injection_style"),
                        "classify_exception": self._output_for("classify_exception"),
                    }
                }
                for step in selector.select(ready.steps[0], ready.steps)
            }
        )

        self.assertEqual(completed.status, "done", completed.error)
        results = self._aggregate_result(started.run_id).rule_results
        self.assertEqual(len(results), 2)
        result = next(
            result for result in results if result.provenance.source_index == 1
        )
        self.assertEqual(
            [metric.value for metric in result.metrics],
            [2, 8, 2, 2, "concrete", 0, 1, 1, 1, 1],
        )
        self.assertTrue(
            all(
                metric.derivation is not None
                for metric in result.metrics
                if metric.metric_id != "SUI-5"
            )
        )

    def _events(self, run_id: str) -> list[dict[str, object]]:
        events_path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
