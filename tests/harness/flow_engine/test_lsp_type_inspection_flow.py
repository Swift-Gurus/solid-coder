"""Exercises LSP-1 classification, coverage and replay through the bundled rule."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "tests/harness"))

from harness.batch_step_renderer_factory import BatchStepRendererFactory
from bundled_review_rule_policy_writer import BundledReviewRulePolicyWriter
from harness.event_replayer import EventParser
from harness.project_context import ProjectDirectory
from harness.rule_review_result import RuleReviewResult
from harness.sibling_batch_step_selector_factory import SiblingBatchStepSelectorFactory
from harness.step_completed_event import StepCompletedEvent
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from review.review_operation_registrations_factory import ReviewOperationRegistrationsFactory
from source.analysis.provenance.resolved_type_inspections import ResolvedTypeInspections
from source.analysis.provenance.source_type_inspection_operation import SourceTypeInspectionOperation
from source.source_operation_registrations_factory import SourceOperationRegistrationsFactory
from source.text_analysis_source import TextAnalysisSource


class TestLSPTypeInspectionFlow(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="lsp-inspection-flow-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".git").mkdir()
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.root, plugin_root=ROOT,
            registrations=[
                *SourceOperationRegistrationsFactory(ProjectDirectory(path=self.root)).make(),
                *ReviewOperationRegistrationsFactory().make(),
            ],
        )
        self.driver.workflow_path = ROOT / "workflows/review/rules/lsp/workflow.yaml"

    def start(self, body="_ = value as? Concrete", aggregate=False):
        self.source = (
            "import Foundation\nprotocol Service {}\nstruct Concrete: Service {}\n"
            "struct Consumer { func inspect(_ value: any Service, _ response: URLResponse) {\n"
            + body + "\n} }\n"
        )
        self.path = self.root / "Unwritten.swift"
        prepared = PrepareReviewOperationFactory().make().execute(PrepareReviewInput(
            target=TextAnalysisSource(text=self.source, virtual_path=str(self.path)),
        ))
        unit = next(unit for unit in prepared.units if unit.target.name == "Consumer")
        if aggregate:
            self.driver.workflow_path = self.root / "aggregate.yaml"
            self.driver.write_workflow("""
id: aggregate-lsp-test
name: Aggregate bundled LSP
max_turns: 24
steps:
  - group: reviews
    execution: {mode: aggregate}
    presentation: {mode: combined}
    steps:
      - include: {workflow: lsp}
        as: lsp_review
        with:
          review_unit: "{{params.review_unit}}"
          source_context: "{{params.source_context}}"
""")
        started = self.driver.start(params={
            "review_unit": unit.model_dump(mode="json"),
            "source_context": prepared.source_context.model_dump(mode="json"),
        })
        self.assertIsNone(started.error, started.error)
        self.run_id = started.run_id
        self.assertFalse(self.path.exists())
        return started

    def local_id(self, step):
        return step.batch.authored_step.step_id if step.batch is not None and step.batch.mode.value == "aggregate" else step.step_id

    def add(self, submissions, step, payload):
        if step.batch is None:
            submissions[step.instance_id] = payload
        elif step.batch.mode.value == "aggregate":
            submissions.setdefault(step.batch.label, {}).setdefault(step.batch.workflow_alias, {})[step.batch.authored_step.step_id] = payload
        elif step.batch.mode.value == "combined_rules":
            submissions.setdefault(step.batch.label, {})[step.batch.rule_alias] = payload
        else:
            submissions[step.batch.label] = payload

    def payload(self, step, classification):
        local = self.local_id(step)
        if local.endswith("classify_type_inspections"):
            return {"classification": classification, "additional_info": {
                "reasoning": "Classified the inspection's purpose using recorded ownership.",
                "evidence": "The supplied expression in Consumer.inspect.",
            }}
        if local.endswith("analyze_substitutability"):
            return {"has_inheritance": False, "relationship_terms": ["Consumer"], "contract_implementations": []}
        if local.endswith("classify_relationship_violations"):
            return {"observations": []}
        self.assertTrue(local.endswith("classify_exception"), local)
        return {"is_exception": False, "additional_info": {"reasoning": "Not a NoOp object.", "evidence": "Consumer.inspect has behavior."}}

    def finish(self, ready, classification="ABSTRACTION_BYPASS", expected_results=1, source_index=0):
        for _ in range(12):
            self.assertIsNone(ready.error, ready.error)
            if ready.status == "done":
                break
            self.assertTrue(ready.steps)
            submissions = {}
            selected = ready.steps[0]
            shown = SiblingBatchStepSelectorFactory().make().select(selected, ready.steps) if selected.batch is not None else [selected]
            for step in shown:
                self.add(submissions, step, self.payload(step, classification))
            ready = self.driver.advance(submissions)
        self.assertEqual(ready.status, "done", ready.error)
        paths = list((self.root / "runs" / self.run_id / "results/review/lsp").rglob("result.json"))
        self.assertEqual(len(paths), expected_results)
        results = [RuleReviewResult.model_validate_json(path.read_text()) for path in paths]
        return next(result for result in results if result.provenance.source_index == source_index)

    def classifiers(self, ready):
        return [step for step in ready.steps if self.local_id(step).endswith("classify_type_inspections")]

    def completions(self):
        path = self.root / "runs" / self.run_id / "events.jsonl"
        return [StepCompletedEvent.model_validate(event) for event in EventParser().parse(path.read_text().splitlines()) if event.get("event") == "step_completed"]

    def inspections(self):
        event = next(event for event in self.completions() if (event.local_step_id or event.step_id).endswith("prepare_type_inspections"))
        return ResolvedTypeInspections.model_validate(event.outputs)

    def test_verified_owned_bypass_is_counted_by_mcp(self):
        ready = self.start()
        self.assertEqual(len(self.classifiers(ready)), 1)
        result = self.finish(ready)
        self.assertEqual(result.metrics[0].metric_id, "LSP-1")
        self.assertEqual(result.metrics[0].value, 1)
        self.assertEqual(result.metrics[0].severity.value, "SEVERE")
        self.assertEqual(result.unavailable_metrics, [])
        self.assertTrue(self.inspections().inspections[0].verified)

    def test_external_narrowing_and_diagnostic_classifications_do_not_count(self):
        for body, classification in [
            ("_ = response as? HTTPURLResponse", "REQUIRED_EXTERNAL_NARROWING"),
            ("print(type(of: value))", "NON_BEHAVIORAL_INSPECTION"),
        ]:
            with self.subTest(classification=classification):
                result = self.finish(self.start(body), classification)
                self.assertEqual(result.metrics[0].value, 0)
                self.assertEqual(result.unavailable_metrics, [])

    def test_unknown_semantic_evidence_is_unavailable_without_a_classifier(self):
        ready = self.start("let inferred = value; _ = inferred as? Concrete")
        self.assertEqual(self.classifiers(ready), [])
        result = self.finish(ready)
        self.assertFalse(any(metric.metric_id == "LSP-1" for metric in result.metrics))
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["LSP-1"])

    def test_known_violation_survives_incomplete_semantic_coverage(self):
        result = self.finish(self.start("_ = value as? Concrete; let inferred = value; _ = inferred as? Concrete"))
        confirmed = next(metric for metric in result.metrics if metric.metric_id == "LSP-1")
        self.assertEqual(confirmed.observation_id, "confirmed_partial")
        self.assertEqual(confirmed.value, 1)
        self.assertEqual(confirmed.severity.value, "SEVERE")
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["LSP-1"])

    def test_model_uncertainty_does_not_become_compliant_zero(self):
        result = self.finish(self.start(), "UNABLE_TO_VERIFY")
        self.assertFalse(any(metric.metric_id == "LSP-1" for metric in result.metrics))
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["LSP-1"])

    def test_empty_complete_inventory_skips_classification(self):
        ready = self.start("print(value)")
        self.assertEqual(self.classifiers(ready), [])
        result = self.finish(ready)
        self.assertEqual(result.metrics[0].value, 0)
        self.assertEqual(result.unavailable_metrics, [])

    def test_batch_renders_compact_facts_once_without_full_source_or_internal_paths(self):
        ready = self.start("_ = value as? Concrete; _ = value is Concrete")
        steps = self.classifiers(ready)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].prompt, steps[1].prompt)
        text = BatchStepRendererFactory().make().render(steps)
        self.assertNotIn(self.source, text)
        self.assertNotIn(str(self.root), text)
        self.assertEqual(text.count("Classify the purpose"), 1)
        self.finish(ready)

    def test_missing_invalid_and_stale_labels_recover_without_repeating_lookup(self):
        with patch.object(SourceTypeInspectionOperation, "execute", autospec=True, side_effect=SourceTypeInspectionOperation.execute) as lookup:
            ready = self.start("_ = value as? Concrete; _ = value is Concrete")
            classifiers = self.classifiers(ready)
            self.assertEqual(len(classifiers), 2)
            rejected = self.driver.advance({"invented-inspection": {"classification": "ABSTRACTION_BYPASS"}})
            self.assertTrue(rejected.error)
            bad = self.driver.advance({classifiers[0].batch.label: {"classification": "INVALID"}})
            self.assertTrue(any(step.rejection_reason for step in self.classifiers(bad)))
            first = {classifiers[0].batch.label: self.payload(classifiers[0], "ABSTRACTION_BYPASS")}
            pending = self.driver.advance(first)
            self.assertEqual(len(self.classifiers(pending)), 1)
            self.assertFalse(any((event.local_step_id or event.step_id) == "type_checks" for event in self.completions()))
            stale = self.driver.advance(first)
            self.assertTrue(stale.error)
            result = self.finish(self.driver.advance())
            self.assertEqual(result.metrics[0].value, 2)
            self.assertEqual(lookup.call_count, 1)

    def test_aggregate_scores_real_rule_after_mcp_boundary_and_replays_original_facts(self):
        with patch.object(SourceTypeInspectionOperation, "execute", autospec=True, side_effect=SourceTypeInspectionOperation.execute) as lookup:
            ready = self.start(aggregate=True)
            self.assertTrue(self.classifiers(ready))
            before = self.inspections()
            config = self.root / ".solid-coder/config.toml"
            config.parent.mkdir(exist_ok=True)
            config.write_text('[hooks.pre_write_gate]\nexclude = ["**/*.swift"]\n')
            result = self.finish(ready)
            self.assertEqual(result.metrics[0].value, 1)
            self.assertEqual(self.inspections(), before)
            self.assertEqual(lookup.call_count, 1)

    def test_aggregate_scores_sdk_call_classification_with_verified_return_contract(self):
        with patch.object(SourceTypeInspectionOperation, "execute", autospec=True, side_effect=SourceTypeInspectionOperation.execute) as lookup:
            ready = self.start(
                'let cache = NSCache<NSString, AnyObject>(); '
                '_ = cache.object(forKey: NSString(string: "key")) as? Data',
                aggregate=True,
            )
            self.assertEqual(len(self.classifiers(ready)), 1)
            before = self.inspections()
            self.assertEqual(before.limitations, [])
            self.assertTrue(before.inspections[0].verified)
            self.assertEqual(before.inspections[0].contract.ownership, "external")
            self.assertNotEqual(
                before.inspections[0].value.resolution.symbol_id,
                before.inspections[0].contract.resolution.symbol_id,
            )
            result = self.finish(ready, "REQUIRED_EXTERNAL_NARROWING")
            metric = next(metric for metric in result.metrics if metric.metric_id == "LSP-1")
            self.assertEqual(metric.value, 0)
            self.assertEqual(result.unavailable_metrics, [])
            self.assertEqual(self.inspections(), before)
            self.assertEqual(lookup.call_count, 1)

    def test_real_aggregate_bundle_keeps_two_units_classifications_separate(self):
        BundledReviewRulePolicyWriter(plugin_root=ROOT, project_root=self.root).write_only("lsp")
        self.driver.workflow_path = ROOT / "workflows/review/bundles/solid-file-review-aggregate/workflow.yaml"
        source = """protocol Service {}
struct Concrete: Service {}
struct First { func inspect(_ value: any Service) { _ = value as? Concrete } }
struct Second { func inspect(_ value: any Service) { _ = value is Concrete } }
"""
        started = self.driver.start(params={
            "target": TextAnalysisSource(text=source, virtual_path=str(self.root / "Source.swift")).model_dump(mode="json"),
            "context_sources": [],
        })
        self.run_id = started.run_id
        result = self.finish(started, expected_results=4, source_index=2)
        self.assertEqual(result.metrics[0].value, 1)
        paths = list((self.root / "runs" / self.run_id / "results/review/lsp").rglob("result.json"))
        results = [RuleReviewResult.model_validate_json(path.read_text()) for path in paths]
        self.assertEqual([entry.metrics[0].value for entry in sorted(results, key=lambda entry: entry.provenance.source_index)], [0, 0, 1, 1])
