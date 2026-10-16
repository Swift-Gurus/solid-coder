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
from source.prepare_search_targets_operation_factory import PrepareSearchTargetsOperationFactory
from source.search_target_granularity import SearchTargetGranularity
from source.source_operation_registrations_factory import SourceOperationRegistrationsFactory
from source.source_search_context import SourceSearchContext


"""
solid-name: TestISPExtensionReviewFlow
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies deterministic combined interface width and independently scored extension responsibilities through aggregate submission, recovery, and replay.
"""
class TestISPExtensionReviewFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.root,
            registrations=SourceOperationRegistrationsFactory(ProjectDirectory(path=self.root)).make(),
            plugin_root=_PROJECT_ROOT,
        )
        self.driver.workflow_path = (
            _PROJECT_ROOT / "workflows" / "review" / "rules" / "isp" / "workflow.yaml"
        )

    def start_review(self, requirements: list[str], extensions: list[str], conformer_source: str | None = "struct Store: Reading { func conformerOnly() {} }\n") -> FlowNextResult:
        interface = self.root / "Reading.swift"
        extension = self.root / "Reading+Behavior.swift"
        conformer = self.root / "Store.swift"
        interface.write_text("protocol Reading {\n" + "\n".join(requirements) + "\n}\n", encoding="utf-8")
        extension.write_text("extension Reading {\n" + "\n".join(extensions) + "\n}\n", encoding="utf-8")
        self.sources = [interface, extension]
        if conformer_source is not None:
            conformer.write_text(conformer_source, encoding="utf-8")
            self.sources.append(conformer)
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(source=FileAnalysisSource(path=interface), granularity=SearchTargetGranularity.UNIT),
        )
        started = self.driver.start(params={
            "review_unit": NormalizedReviewUnit(
                target=prepared.targets[0],
                applicability=RuleApplicabilityContext(file_extension=".swift", unit_kind="protocol", tags=[]),
                tag_evidence=[],
            ).model_dump(mode="json"),
            "source_context": SourceSearchContext(sources=[prepared.snapshot]).model_dump(mode="json"),
        })
        self.assertIsNone(started.error, started.error)
        self.run_id = started.run_id
        extensions = [step for step in started.steps if step.step_id == "classify_extension_members"]
        return FlowNextResult(status=started.status, steps=extensions or started.steps, error=started.error)

    def classify(self, ready: FlowNextResult, classification: str = "SAME_RESPONSIBILITY") -> FlowNextResult:
        result = self.driver.advance({step.batch.label: {
            "assessment": {
                "classification": classification,
                "is_exception": False,
                "additional_info": {
                    "reasoning": "The implementation's responsibility was compared with the interface.",
                    "evidence": "Reading+Behavior.swift contains the inspected member.",
                },
            },
            "availability": {
                "observation_id": step.batch.label, "matches": classification != "UNABLE_TO_VERIFY", "included": True,
                "reasoning": "The supplied implementation was inspected.", "evidence": "Reading+Behavior.swift",
            },
        } for step in ready.steps})
        extensions = [step for step in result.steps if step.step_id == "classify_extension_members"]
        return replace(result, steps=extensions) if extensions else result

    def finish(self, ready: FlowNextResult) -> RuleReviewResult:
        self.assertIsNone(ready.error, ready.error)
        candidates = [step for step in ready.steps if step.step_id.endswith("classify_candidate")]
        if candidates:
            ready = self.driver.advance({step.instance_id: {
                "availability": {
                    "observation_id": "Store", "included": True, "matches": False,
                    "reasoning": "The supplied conformer has insufficient implementation evidence.", "evidence": "Store.swift",
                },
                "coverage_entries": [],
            } for step in candidates})
            self.assertIsNone(ready.error, ready.error)
        self.assertEqual([step.step_id for step in ready.steps], ["classify_exception"])
        step = ready.steps[0]
        completed = self.driver.advance({step.instance_id: {
            "is_exception": False,
            "additional_info": {"reasoning": "No whole-interface exception applies.", "evidence": "Reading declares behavioral requirements."},
        }})
        self.assertEqual(completed.status, "done", completed.error)
        path = self.root / "runs" / self.run_id / "results" / "review" / "isp" / self.run_id / "result.json"
        return RuleReviewResult.model_validate_json(path.read_text(encoding="utf-8"))

    def completions(self) -> list[StepCompletedEvent]:
        path = self.root / "runs" / self.run_id / "events.jsonl"
        return [StepCompletedEvent.model_validate(event)
                for event in EventParser().parse(path.read_text().splitlines())
                if event.get("event") == "step_completed"]

    def test_combined_width_counts_requirements_and_additional_extension_members(self) -> None:
        ready = self.start_review(
            [f"func read{index}()" for index in range(6)],
            [f"func extra{index}() {{}}" for index in range(3)],
        )
        self.assertEqual(len(ready.steps), 3)
        self.assertEqual([event.step_id for event in self.completions()].count("discover"), 1)
        self.assertIn("width", [event.step_id for event in self.completions()])

        result = self.finish(self.classify(ready))

        width = next(metric for metric in result.metrics if metric.metric_id == "ISP-1")
        self.assertEqual(width.value, 9)
        self.assertEqual(width.severity.value, "SEVERE")

    def test_default_implementations_do_not_double_count_requirements(self) -> None:
        ready = self.start_review(
            [f"func read{index}()" for index in range(6)],
            [f"func read{index}() {{}}" for index in range(6)],
        )

        result = self.finish(self.classify(ready))

        width = next(metric for metric in result.metrics if metric.metric_id == "ISP-1")
        self.assertEqual(width.value, 6)
        self.assertEqual(width.severity.value, "MINOR")

    def test_mixed_responsibilities_are_severe_below_width_threshold(self) -> None:
        ready = self.start_review(
            [f"func read{index}()" for index in range(3)],
            ["func save() {}", "func delete() {}"],
        )

        result = self.finish(self.classify(ready, "INDEPENDENT_RESPONSIBILITY"))

        width = next(metric for metric in result.metrics if metric.metric_id == "ISP-1")
        responsibilities = next(metric for metric in result.metrics if metric.metric_id == "ISP-4")
        self.assertEqual(width.value, 5)
        self.assertEqual(width.severity.value, "COMPLIANT")
        self.assertEqual(responsibilities.value, 2)
        self.assertEqual(responsibilities.severity.value, "SEVERE")

    def test_private_and_conformer_only_members_do_not_reach_judgment_or_width(self) -> None:
        ready = self.start_review(
            ["func read()"],
            ["func readMore() {}", "private func hidden() {}", "fileprivate func helper() {}"],
        )
        self.assertEqual(len(ready.steps), 1)
        self.assertIn("readMore", ready.steps[0].prompt)
        for name in ["hidden", "helper", "conformerOnly"]:
            self.assertNotIn(name, ready.steps[0].prompt)

        result = self.finish(self.classify(ready))

        self.assertEqual(next(metric.value for metric in result.metrics if metric.metric_id == "ISP-1"), 2)
        self.assertEqual(result.severity.value, "COMPLIANT")

    def test_overloads_remain_distinct_while_matching_default_counts_once(self) -> None:
        ready = self.start_review(
            ["func read(id: Int) -> String", "func read(id: String) -> String"],
            ['func read(id value: Int) -> String { "ok" }', 'func read(flag: Bool) -> String { "ok" }'],
        )

        result = self.finish(self.classify(ready))

        self.assertEqual(next(metric.value for metric in result.metrics if metric.metric_id == "ISP-1"), 3)

    def test_partial_submission_preserves_accepted_members_and_waits_for_scoring(self) -> None:
        ready = self.start_review(["func read()"], ["func first() {}", "func second() {}"])
        pending = self.classify(replace(ready, steps=ready.steps[:1]))
        self.assertEqual(len(pending.steps), 1)
        self.assertNotIn("mixed_responsibilities", [event.step_id for event in self.completions()])

        result = self.finish(self.classify(pending))

        self.assertEqual(result.severity.value, "COMPLIANT")
        self.assertEqual([event.step_id for event in self.completions()].count("members"), 1)

    def test_invalid_classification_can_be_corrected_without_repeating_source_operations(self) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])
        pending = self.classify(ready, "INVALID")
        self.assertEqual(len(pending.steps), 1)
        self.assertIsNotNone(pending.steps[0].rejection_reason)

        result = self.finish(self.classify(pending))

        self.assertEqual(result.severity.value, "COMPLIANT")
        self.assertEqual([event.step_id for event in self.completions()].count("members"), 1)

    def test_replay_preserves_width_and_classification_inputs_without_source_files(self) -> None:
        ready = self.start_review(["func read()"], ["func extra() {}"])
        before = self.completions()
        for source in self.sources:
            source.unlink()

        result = self.finish(self.classify(ready))

        self.assertEqual(next(metric.value for metric in result.metrics if metric.metric_id == "ISP-1"), 2)
        self.assertEqual(self.completions()[:len(before)], before)

    def test_width_severity_boundaries_are_inclusive(self) -> None:
        for count, severity in [(5, "COMPLIANT"), (6, "MINOR"), (8, "MINOR"), (9, "SEVERE")]:
            with self.subTest(count=count):
                ready = self.start_review(
                    [f"func read{index}()" for index in range(count - 1)],
                    ["func extra() {}"],
                )

                result = self.finish(self.classify(ready))

                width = next(metric for metric in result.metrics if metric.metric_id == "ISP-1")
                self.assertEqual(width.value, count)
                self.assertEqual(width.severity.value, severity)

    def test_no_exposed_extensions_requires_no_member_classification(self) -> None:
        for extensions in [[], ["private func hidden() {}"]]:
            with self.subTest(extensions=extensions):
                ready = self.start_review(["func read()"], extensions)

                result = self.finish(ready)

                self.assertEqual(next(metric.value for metric in result.metrics if metric.metric_id == "ISP-1"), 1)
                self.assertEqual(next(metric.value for metric in result.metrics if metric.metric_id == "ISP-4"), 0)
                self.assertEqual(result.severity.value, "COMPLIANT")

    def test_first_interface_preserves_width_and_unavailable_usage_metrics(self) -> None:
        ready = self.start_review(["func read()"], [], conformer_source=None)

        result = self.finish(ready)

        self.assertEqual([(metric.metric_id, metric.value) for metric in result.metrics], [("ISP-1", 1), ("ISP-4", 0)])
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["ISP-2", "ISP-3"])
        self.assertTrue(all(metric.additional_info.reasoning and metric.additional_info.evidence for metric in result.unavailable_metrics))

    def test_unknown_extension_judgment_is_not_a_compliant_measurement(self) -> None:
        ready = self.start_review([f"func read{index}()" for index in range(9)], ["func extra() {}"])

        result = self.finish(self.classify(ready, "UNABLE_TO_VERIFY"))

        self.assertEqual([(metric.metric_id, metric.value) for metric in result.metrics], [("ISP-1", 10)])
        self.assertEqual(result.severity.value, "SEVERE")
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["ISP-2", "ISP-3", "ISP-4"])

    def test_empty_interface_has_measured_zero_width(self) -> None:
        ready = self.start_review([], [], conformer_source=None)

        result = self.finish(ready)

        self.assertEqual(next(metric.value for metric in result.metrics if metric.metric_id == "ISP-1"), 0)

    def test_aggregate_submission_scores_real_bundled_rule_across_operation_boundaries(self) -> None:
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
        ready = self.start_review([f"func read{index}()" for index in range(4)], ["func save() {}", "func delete() {}"])
        combined_extension_count = 0
        for _ in range(8):
            if ready.status == "done":
                break
            self.assertIsNone(ready.error, ready.error)
            submissions = {}
            first_batch = ready.steps[0].batch
            selected = [step for step in ready.steps if
                        (step.batch is None if first_batch is None else step.batch is not None and step.batch.group == first_batch.group)]
            for step in selected:
                if step.batch is not None and step.batch.mode.value == "aggregate":
                    authored = step.batch.authored_step.step_id
                else:
                    authored = next(name for name in ["classify_candidate", "classify_extension_members", "classify_exception"] if step.step_id.endswith(name))
                info = {"reasoning": "Inspected the supplied declaration.", "evidence": "Reading.swift and Reading+Behavior.swift"}
                if authored == "classify_extension_members":
                    combined_extension_count += 1
                    payload = {
                        "assessment": {"classification": "INDEPENDENT_RESPONSIBILITY", "is_exception": False, "additional_info": info},
                        "availability": {"observation_id": step.batch.label, "matches": True, "included": True, **info},
                    }
                elif authored == "classify_candidate":
                    payload = {
                        "availability": {"observation_id": "Store", "matches": False, "included": True, **info},
                        "coverage_entries": [],
                    }
                else:
                    self.assertEqual(authored, "classify_exception")
                    payload = {"is_exception": False, "additional_info": info}
                if step.batch is None:
                    submissions[step.instance_id] = payload
                elif step.batch.mode.value == "aggregate":
                    submissions.setdefault(step.batch.label, {}).setdefault(step.batch.workflow_alias, {})[authored] = payload
                elif step.batch.mode.value == "combined_rules":
                    submissions.setdefault(step.batch.label, {})[step.batch.rule_alias] = payload
                else:
                    submissions[step.batch.label] = payload
            if any(step.step_id.endswith("classify_extension_members") for step in selected):
                self.assertEqual(len(selected), 2)
            ready = self.driver.advance(submissions)
        self.assertEqual(ready.status, "done", ready.error)
        paths = list((self.root / "runs" / self.run_id / "results/review/isp").rglob("result.json"))
        self.assertEqual(len(paths), 1)
        result = RuleReviewResult.model_validate_json(paths[0].read_text())
        self.assertEqual([(metric.metric_id, metric.value) for metric in result.metrics], [("ISP-1", 6), ("ISP-4", 2)])
        self.assertEqual(result.severity.value, "SEVERE")
        self.assertEqual(combined_extension_count, 2)
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["ISP-2", "ISP-3"])
        self.assertEqual([event.local_step_id for event in self.completions()].count("discover"), 1)
        self.assertEqual([event.local_step_id for event in self.completions()].count("members"), 1)
