"""Runs the real bundled LSP migration against both locked model profiles."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "tests/harness"))

from claude_test_base import ClaudeTestBase
from codex_test_base import CodexTestBase
from harness.event_replayer import EventParser
from harness.review_result import ReviewResult
from harness.step_completed_event import StepCompletedEvent
from rule_validation_e2e_live_base import RuleValidationE2ELiveBase
from source.analysis.provenance.resolved_type_inspections import ResolvedTypeInspections
from source.analysis.provenance.source_type_inspection_provenance import SourceTypeInspectionProvenance


class LSPTypeInspectionLiveBase(RuleValidationE2ELiveBase):
    __test__ = False
    WORKFLOW_ID = "lsp"
    REVIEW_WORKFLOW_ID = "solid-file-review-aggregate"
    ARTIFACT_SCENARIO = "lsp-type-inspections"
    FIXTURE = ROOT / "tests/principles/LSP/fixtures/fixture-4.swift"

    def assert_workflow(self, run):
        self._assert_codex_protocol(run)
        events = EventParser().parse((run.run_directory / "events.jsonl").read_text().splitlines())
        self.assertEqual(events[-1]["event"], "run_completed")
        self.assertFalse({event.get("event") for event in events} & {"step_attempt_failed", "step_rejected", "run_failed"})
        review = ReviewResult.model_validate_json((run.run_directory / "results/review/result.json").read_text())
        self.assertEqual(len(review.rule_results), 3)
        result = next(result for result in review.rule_results if result.provenance.source_index == 2)
        self.assertEqual(result.workflow_id, "lsp")
        self.assertFalse(result.exception.is_exception)
        self.assertEqual(result.severity.value, "SEVERE")
        self.assertEqual([(metric.metric_id, metric.observation_id, metric.value) for metric in result.metrics], [
            ("LSP-1", "confirmed_partial", 1), ("LSP-2", "value", 0),
            ("LSP-3", "value", 0), ("LSP-4", "value", 0),
        ])
        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["LSP-1"])
        completed = [StepCompletedEvent.model_validate(event) for event in events
                     if event.get("event") == "step_completed" and event.get("workflow_instance_id") == result.rule_instance_id]
        preparations = [event for event in completed if event.local_step_id == "prepare_type_inspections"]
        self.assertEqual(len(preparations), 1)
        facts = ResolvedTypeInspections.model_validate(preparations[0].outputs)
        self.assertEqual([fact.verified for fact in facts.inspections], [True, True, True, False])
        classifications = [event for event in completed if event.local_step_id == "classify_type_inspections"]
        self.assertEqual(len(classifications), 3)
        self.assertTrue(all(event.iteration_index is not None for event in classifications))
        classifications.sort(key=lambda event: event.iteration_index)
        self.assertEqual({SourceTypeInspectionProvenance.model_validate(event.item).inspection.identity for event in classifications},
                         {fact.inspection.identity for fact in facts.inspections if fact.verified})
        self.assertEqual([event.outputs["classification"] for event in classifications], [
            "ABSTRACTION_BYPASS", "REQUIRED_EXTERNAL_NARROWING", "NON_BEHAVIORAL_INSPECTION",
        ])
        for event in classifications:
            info = event.outputs["additional_info"]
            self.assertTrue(info["reasoning"])
            self.assertTrue(info["evidence"])
            self.assertLess(completed.index(preparations[0]), completed.index(event))
        print(f"LSP semantic/classification evidence: {run.run_directory}")


class TestCodexLSPTypeInspectionLive(CodexTestBase, LSPTypeInspectionLiveBase):
    __test__ = True


class TestClaudeLSPTypeInspectionLive(ClaudeTestBase, LSPTypeInspectionLiveBase):
    __test__ = True
