import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.event_replayer import EventParser
from harness.flow_next_result import FlowNextResult
from harness.project_context import ProjectDirectory
from harness.rule_applicability_context import RuleApplicabilityContext
from harness.rule_review_result import RuleReviewResult
from harness.step_completed_event import StepCompletedEvent
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from review.normalized_review_unit import NormalizedReviewUnit
from source.file_analysis_source import FileAnalysisSource
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from source.source_search_context import SourceSearchContext

"""
solid-name: TestISPExtensionReviewFlow
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies combined interface width, responsibility and stakeholder scoring through the bundled workflow, complete member accounting, recovery, and replay.
"""


class TestISPExtensionReviewFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.root,
            registrations=SourceOperationRegistrationsFactory(
                ProjectDirectory(path=self.root)
            ).make(),
            plugin_root=_PROJECT_ROOT,
        )
        self.driver.workflow_path = (
            _PROJECT_ROOT / "workflows/review/rules/isp/workflow.yaml"
        )

    def start_review(
        self,
        requirements: list[str],
        extensions: list[str],
        target_extension: bool = False,
        definition_kind: str = "protocol",
    ) -> FlowNextResult:
        interface = self.root / "Reading.swift"
        extension = self.root / "Reading+Behavior.swift"
        conformer = self.root / "Store.swift"
        interface.write_text(
            f"{definition_kind} Reading {{\n" + "\n".join(requirements) + "\n}\n",
            encoding="utf-8",
        )
        extension.write_text(
            "extension Reading {\n" + "\n".join(extensions) + "\n}\n", encoding="utf-8"
        )
        conformer.write_text(
            "struct Store: Reading { func conformerOnly() {} }\n", encoding="utf-8"
        )
        self.sources = [interface, extension, conformer]
        prepared = (
            PrepareSearchTargetsOperationFactory()
            .make()
            .execute(
                PrepareSearchTargetsInput(
                    source=FileAnalysisSource(
                        path=extension if target_extension else interface
                    ),
                    granularity=SearchTargetGranularity.UNIT,
                ),
            )
        )
        started = self.driver.start(
            params={
                "review_unit": NormalizedReviewUnit(
                    target=prepared.targets[0],
                    applicability=RuleApplicabilityContext(
                        file_extension=".swift",
                        unit_kind=prepared.targets[0].kind,
                        tags=[],
                    ),
                    tag_evidence=[],
                ).model_dump(mode="json"),
                "source_context": SourceSearchContext(
                    sources=[prepared.snapshot]
                ).model_dump(mode="json"),
            }
        )
        self.assertIsNone(started.error, started.error)
        self.run_id = started.run_id
        return FlowNextResult(
            status=started.status, steps=started.steps, error=started.error
        )

    def classify(
        self,
        ready: FlowNextResult,
        responsibilities: list[str] | None = None,
        stakeholders: list[str] | None = None,
        verification: str = "VERIFIED",
        excepted: bool = False,
    ) -> FlowNextResult:
        submissions = {}
        for index, step in enumerate(ready.steps):
            self.assertTrue(step.step_id.endswith("classify_members"))
            info = {
                "reasoning": "Classified the supplied member's independent concern.",
                "evidence": "The exact supplied member declaration.",
            }
            assessment = {"verification": verification, "additional_info": info}
            if verification != "UNABLE_TO_VERIFY":
                assessment.update(
                    {
                        "action": "read",
                        "responsibility": responsibilities[index]
                        if responsibilities
                        else "reading",
                        "stakeholder": stakeholders[index]
                        if stakeholders
                        else "reader",
                        "is_exception": excepted,
                    }
                )
            self.add_submission(submissions, step, {"assessment": assessment})
        return self.driver.advance(submissions)

    def add_submission(self, submissions, step, payload) -> None:
        if step.batch is None:
            submissions[step.instance_id] = payload
        elif step.batch.mode.value == "aggregate":
            submissions.setdefault(step.batch.label, {}).setdefault(
                step.batch.workflow_alias, {}
            )[step.batch.authored_step.step_id] = payload
        elif step.batch.mode.value == "combined_rules":
            submissions.setdefault(step.batch.label, {})[step.batch.rule_alias] = (
                payload
            )
        else:
            submissions[step.batch.label] = payload

    def finish(self, ready: FlowNextResult, excepted: bool = False) -> RuleReviewResult:
        self.assertIsNone(ready.error, ready.error)
        self.assertEqual(len(ready.steps), 1)
        self.assertTrue(ready.steps[0].step_id.endswith("classify_exception"))
        submissions = {}
        self.add_submission(
            submissions,
            ready.steps[0],
            {
                "is_exception": excepted,
                "additional_info": {
                    "reasoning": "Marker used only for type discrimination."
                    if excepted
                    else "No whole-interface exception applies.",
                    "evidence": "The supplied Reading declaration.",
                },
            },
        )
        completed = self.driver.advance(submissions)
        self.assertEqual(completed.status, "done", completed.error)
        paths = list(
            (self.root / "runs" / self.run_id / "results/review/isp").rglob(
                "result.json"
            )
        )
        self.assertEqual(len(paths), 1)
        return RuleReviewResult.model_validate_json(
            paths[0].read_text(encoding="utf-8")
        )

    def completions(self) -> list[StepCompletedEvent]:
        path = self.root / "runs" / self.run_id / "events.jsonl"
        return [
            StepCompletedEvent.model_validate(event)
            for event in EventParser().parse(path.read_text().splitlines())
            if event.get("event") == "step_completed"
        ]

    def test_combined_width_counts_requirements_and_additional_extension_members(
        self,
    ) -> None:
        ready = self.start_review(
            [f"func read{i}()" for i in range(6)],
            [f"func extra{i}() {{}}" for i in range(3)],
        )

        result = self.finish(self.classify(ready))

        self.assertEqual(len(ready.steps), 9)
        self.assertEqual(
            next(
                metric.value for metric in result.metrics if metric.metric_id == "ISP-1"
            ),
            9,
        )
        self.assertEqual(
            next(
                metric.severity.value
                for metric in result.metrics
                if metric.metric_id == "ISP-1"
            ),
            "SEVERE",
        )

    def test_default_implementations_do_not_double_count_requirements(self) -> None:
        ready = self.start_review(
            [f"func read{i}()" for i in range(6)],
            [f"func read{i}() {{}}" for i in range(6)],
        )

        result = self.finish(self.classify(ready))

        self.assertEqual(len(ready.steps), 12)
        self.assertEqual(
            next(
                metric.value for metric in result.metrics if metric.metric_id == "ISP-1"
            ),
            6,
        )
        self.assertEqual(
            next(
                metric.severity.value
                for metric in result.metrics
                if metric.metric_id == "ISP-1"
            ),
            "MINOR",
        )

    def test_three_distinct_responsibilities_are_severe_and_two_are_compliant(
        self,
    ) -> None:
        for labels, expected in [
            (["reading", "writing", "writing"], "COMPLIANT"),
            (["reading", "writing", "rendering"], "SEVERE"),
        ]:
            with self.subTest(labels=labels):
                ready = self.start_review(
                    ["func read()"], ["func save() {}", "func show() {}"]
                )
                result = self.finish(self.classify(ready, responsibilities=labels))

                metric = next(
                    metric for metric in result.metrics if metric.metric_id == "ISP-3"
                )
                self.assertEqual(metric.value, len(set(labels)))
                self.assertEqual(metric.severity.value, expected)

    def test_two_distinct_stakeholders_are_severe_and_one_is_compliant(self) -> None:
        for labels, expected in [
            (["reader", "reader"], "COMPLIANT"),
            (["reader", "accounting"], "SEVERE"),
        ]:
            with self.subTest(labels=labels):
                ready = self.start_review(["func read()"], ["func save() {}"])
                result = self.finish(self.classify(ready, stakeholders=labels))

                metric = next(
                    metric for metric in result.metrics if metric.metric_id == "ISP-5"
                )
                self.assertEqual(metric.value, len(set(labels)))
                self.assertEqual(metric.severity.value, expected)

    def test_excepted_member_observations_do_not_inflate_classification_counts(
        self,
    ) -> None:
        ready = self.start_review(["func read()"], ["func save() {}", "func show() {}"])

        result = self.finish(
            self.classify(
                ready,
                responsibilities=["reading", "writing", "rendering"],
                stakeholders=["reader", "accounting", "reporting"],
                excepted=True,
            )
        )

        self.assertEqual(
            [
                metric.value
                for metric in result.metrics
                if metric.metric_id in {"ISP-3", "ISP-5"}
            ],
            [0, 0],
        )

    def test_private_and_conformer_only_members_do_not_reach_judgment_or_width(
        self,
    ) -> None:
        ready = self.start_review(
            ["func read()"],
            [
                "func extra() {}",
                "private func hidden() {}",
                "fileprivate func helper() {}",
            ],
        )

        result = self.finish(self.classify(ready))

        self.assertEqual(len(ready.steps), 2)
        for excluded in ["func hidden()", "func helper()", "func conformerOnly()"]:
            self.assertNotIn(excluded, ready.steps[0].prompt)
        self.assertEqual(
            next(
                metric.value for metric in result.metrics if metric.metric_id == "ISP-1"
            ),
            2,
        )

    def test_extension_first_review_supplies_definition_and_extension_together(
        self,
    ) -> None:
        ready = self.start_review(
            ["func read()"], ["func extra() {}"], target_extension=True
        )

        result = self.finish(self.classify(ready))

        self.assertIn("func read()", ready.steps[0].prompt)
        self.assertIn("func extra() {}", ready.steps[0].prompt)
        self.assertEqual(
            next(
                metric.value for metric in result.metrics if metric.metric_id == "ISP-1"
            ),
            2,
        )

    def test_overloads_remain_distinct_while_matching_default_counts_once(self) -> None:
        ready = self.start_review(
            ["func read(id: Int) -> String", "func read(id: String) -> String"],
            [
                'func read(id value: Int) -> String { "ok" }',
                'func read(flag: Bool) -> String { "ok" }',
            ],
        )

        result = self.finish(self.classify(ready))

        self.assertEqual(
            next(
                metric.value for metric in result.metrics if metric.metric_id == "ISP-1"
            ),
            3,
        )

    def test_partial_submission_preserves_accepted_members_and_waits_for_scoring(
        self,
    ) -> None:
        ready = self.start_review(
            ["func read()"], ["func first() {}", "func second() {}"]
        )
        pending = self.classify(replace(ready, steps=ready.steps[:1]))

        self.assertEqual(len(pending.steps), 2)
        self.assertNotIn(
            "responsibilities",
            [event.local_step_id or event.step_id for event in self.completions()],
        )

        result = self.finish(self.classify(pending))
        self.assertEqual(result.severity.value, "COMPLIANT")
        self.assertEqual(
            [
                event.local_step_id or event.step_id for event in self.completions()
            ].count("prepare_context"),
            1,
        )

    def test_invalid_classification_can_be_corrected_without_repeating_source_operations(
        self,
    ) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])
        pending = self.classify(ready, verification="INVALID")

        self.assertTrue(all(step.rejection_reason for step in pending.steps))

        result = self.finish(self.classify(pending))
        self.assertEqual(result.severity.value, "COMPLIANT")
        self.assertEqual(
            [
                event.local_step_id or event.step_id for event in self.completions()
            ].count("prepare_context"),
            1,
        )

    def test_replay_uses_prepared_context_after_source_files_are_removed(self) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])
        before = self.completions()
        for source in self.sources:
            source.unlink()

        result = self.finish(self.classify(ready))

        self.assertEqual(
            next(
                metric.value for metric in result.metrics if metric.metric_id == "ISP-1"
            ),
            2,
        )
        self.assertEqual(self.completions()[: len(before)], before)

    def test_width_severity_boundaries_are_inclusive(self) -> None:
        for count, severity in [
            (5, "COMPLIANT"),
            (6, "MINOR"),
            (8, "MINOR"),
            (9, "SEVERE"),
        ]:
            with self.subTest(count=count):
                ready = self.start_review([f"func read{i}()" for i in range(count)], [])
                result = self.finish(self.classify(ready))

                self.assertEqual(
                    next(
                        metric.severity.value
                        for metric in result.metrics
                        if metric.metric_id == "ISP-1"
                    ),
                    severity,
                )

    def test_no_conformers_are_required_for_responsibility_or_stakeholder_scoring(
        self,
    ) -> None:
        ready = self.start_review(["func read()"], [])

        result = self.finish(self.classify(ready))

        self.assertEqual(
            [(metric.metric_id, metric.value) for metric in result.metrics],
            [("ISP-1", 1), ("ISP-3", 1), ("ISP-5", 1)],
        )
        self.assertEqual(result.unavailable_metrics, [])
        self.assertFalse(
            any(
                (event.local_step_id or event.step_id)
                in {"match", "classify_candidate", "analyze_cohesion"}
                for event in self.completions()
            )
        )

    def test_unverifiable_classification_is_not_a_compliant_measurement(self) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])

        result = self.finish(self.classify(ready, verification="UNABLE_TO_VERIFY"))

        self.assertEqual(
            [(metric.metric_id, metric.value) for metric in result.metrics],
            [("ISP-1", 2)],
        )
        self.assertEqual(
            [metric.metric_id for metric in result.unavailable_metrics],
            ["ISP-3", "ISP-5"],
        )

    def test_ambiguous_extension_definition_preserves_unavailable_metrics(self) -> None:
        (self.root / "Other.swift").write_text("protocol Reading { func other() }\n")
        ready = self.start_review(
            ["func read()"], ["func extra() {}"], target_extension=True
        )

        result = self.finish(ready)

        self.assertEqual(result.metrics, [])
        self.assertEqual(
            [metric.metric_id for metric in result.unavailable_metrics],
            ["ISP-1", "ISP-3", "ISP-5"],
        )

    def test_aggregate_submission_scores_the_real_rule_across_mcp_boundaries(
        self,
    ) -> None:
        self.driver.workflow_path = self.root / "aggregate.yaml"
        self.driver.write_workflow("""
id: aggregate-isp-test
name: Aggregate bundled ISP
max_turns: 10
steps:
  - group: reviews
    execution: {mode: aggregate}
    presentation: {mode: combined}
    steps:
      - include: {workflow: isp}
        as: isp_review
        with:
          review_unit: "{{params.review_unit}}"
          source_context: "{{params.source_context}}"
""")
        ready = self.start_review(["func read()"], ["func save() {}", "func show() {}"])

        result = self.finish(
            self.classify(
                ready,
                responsibilities=["reading", "writing", "rendering"],
                stakeholders=["reader", "accounting", "reader"],
            )
        )

        self.assertEqual(
            [(metric.metric_id, metric.value) for metric in result.metrics],
            [("ISP-1", 3), ("ISP-3", 3), ("ISP-5", 2)],
        )
        self.assertEqual(result.severity.value, "SEVERE")
        self.assertEqual(
            [
                event.local_step_id or event.step_id for event in self.completions()
            ].count("prepare_context"),
            1,
        )

    def test_concrete_extension_is_not_an_interface_review(self) -> None:
        ready = self.start_review(
            [], ["func extra() {}"], target_extension=True, definition_kind="struct"
        )

        self.assertEqual(ready.status, "done", ready.error)
        self.assertEqual(ready.steps, [])
        self.assertFalse(
            (self.root / "runs" / self.run_id / "results/review/isp").exists()
        )

    def test_empty_marker_interface_has_no_invented_member_classification(self) -> None:
        ready = self.start_review([], [])

        result = self.finish(ready, excepted=True)

        self.assertEqual([metric.value for metric in result.metrics], [0, 0, 0])
        self.assertTrue(result.exception.is_exception)
        self.assertEqual(result.unavailable_metrics, [])

    def test_one_unverified_member_prevents_partial_classifications_becoming_scores(
        self,
    ) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])
        pending = self.classify(replace(ready, steps=ready.steps[:1]))

        result = self.finish(self.classify(pending, verification="UNABLE_TO_VERIFY"))

        self.assertEqual(
            [(metric.metric_id, metric.value) for metric in result.metrics],
            [("ISP-1", 2)],
        )
        self.assertEqual(
            [metric.metric_id for metric in result.unavailable_metrics],
            ["ISP-3", "ISP-5"],
        )

    def test_unknown_member_label_is_rejected_without_losing_pending_work(self) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])

        rejected = self.driver.advance({"unknown-member": {"assessment": {}}})

        self.assertTrue(
            rejected.error or any(step.rejection_reason for step in rejected.steps)
        )
        pending = self.driver.advance()
        self.assertEqual(
            [step.instance_id for step in pending.steps],
            [step.instance_id for step in ready.steps],
        )
        result = self.finish(self.classify(pending))
        self.assertEqual([metric.value for metric in result.metrics], [2, 1, 1])
