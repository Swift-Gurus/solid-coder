"""Defines the Codex live smoke contract for the composite review workflow."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import ClassVar

from pydantic import TypeAdapter

_HARNESS = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
for _directory in (_HARNESS, _MCP_SERVER):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness.review_result import ReviewResult  # noqa: E402
from review.prepare_review_input import PrepareReviewInput  # noqa: E402
from source.file_analysis_source import FileAnalysisSource  # noqa: E402
from codex_review_stage_evidence_reader import (  # noqa: E402
    CodexReviewStageEvidenceReader,
)
from codex_transcript_token_usage_reader import (  # noqa: E402
    CodexTranscriptTokenUsageReader,
)
from flow_audit_event import FlowAuditEvent  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_workflow_e2e_live_base import LiveWorkflowE2ELiveBase  # noqa: E402
from live_workflow_scenario import LiveWorkflowScenario  # noqa: E402
from preserved_live_workflow_run import PreservedLiveWorkflowRun  # noqa: E402
from review_comparison_run_evidence import (  # noqa: E402
    ReviewComparisonRunEvidence,
)
from review_comparison_source_project import (  # noqa: E402
    ReviewComparisonSourceProject,
)
from review_comparison_stage_evidence import (  # noqa: E402
    ReviewComparisonStageEvidence,
)
from review_comparison_rule_expectation import (  # noqa: E402
    ReviewComparisonRuleExpectation,
)


_PROJECT_ROOT = _MCP_SERVER.parent
_EXPECTATION_FILE = (
    Path(__file__).parent
    / "fixtures"
    / "review_comparison"
    / "expectation.json"
)
"""
solid-name: SolidReviewComparisonE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Executes and audits the fixed composite workflow-review smoke scenario used before repeated comparison.
"""
class SolidReviewComparisonE2ELiveBase(LiveWorkflowE2ELiveBase):
    PROJECT_ROOT = _PROJECT_ROOT
    EXPECTED_RULE_RESULTS: ClassVar[list[ReviewComparisonRuleExpectation]] = (
        TypeAdapter(list[ReviewComparisonRuleExpectation]).validate_json(
            _EXPECTATION_FILE.read_text(encoding="utf-8")
        )
    )

    def setUp(self) -> None:
        self._source_project = ReviewComparisonSourceProject.create()
        self.addCleanup(self._source_project.cleanup)
        super().setUp()

    @property
    def execution_project_root(self) -> Path:
        return self._source_project.root

    @property
    def scenario(self) -> LiveWorkflowScenario:
        return LiveWorkflowScenario(
            workflow_id="solid-review",
            parameters=PrepareReviewInput(
                target=FileAnalysisSource(
                    path=self._source_project.review_target,
                )
            ),
            artifact_scope=LiveSessionArtifactScope(
                domain="comparison",
                scenario="workflow-smoke",
            ),
            model_context=(
                "Source under review:\n"
                "```swift\n"
                f"{self._source_project.review_target.read_text(encoding='utf-8')}"
                "\n```"
            ),
        )

    def test_workflow_satisfies_its_live_contract(self) -> None:
        started = time.monotonic()
        run = self._run_scenario(self.scenario)
        elapsed_seconds = time.monotonic() - started

        self.assert_workflow(run)
        evidence = self._evidence(run, elapsed_seconds)
        (run.session.artifact_directory / "comparison-evidence.json").write_text(
            evidence.model_dump_json(indent=2),
            encoding="utf-8",
        )
        self.assertTrue(evidence.review_stage.token_usage.available)
        self.assertTrue(evidence.full_run.token_usage.available)

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        result = ReviewResult.model_validate_json(
            (
                run.run_directory
                / "results"
                / "review"
                / "result.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(result.workflow_id, "solid-review")
        self.assertEqual(
            len(result.rule_results),
            len(self.EXPECTED_RULE_RESULTS),
        )
        for actual, expected in zip(
            result.rule_results,
            self.EXPECTED_RULE_RESULTS,
        ):
            self.assertEqual(actual.workflow_id, expected.workflow_id)
            self.assertEqual(
                actual.provenance.source_index,
                expected.source_index,
            )
            self.assertEqual(actual.severity, expected.final_severity)
            self.assertEqual(
                actual.exception.is_exception,
                expected.is_exception,
            )
            self.assertEqual(len(actual.metrics), len(expected.metrics))
            for actual_metric, expected_metric in zip(
                actual.metrics,
                expected.metrics,
            ):
                self.assertEqual(
                    actual_metric.metric_id,
                    expected_metric.metric_id,
                )
                self.assertEqual(
                    actual_metric.observation_id,
                    expected_metric.observation_id,
                )
                self.assertEqual(actual_metric.value, expected_metric.value)
                self.assertEqual(
                    actual_metric.severity,
                    expected_metric.severity,
                )
        self.assertTrue(all(
            rule_result.provenance.kind == "included"
            for rule_result in result.rule_results
        ))
        self._assert_dry_classifications_were_selected(run)
        self._assert_dry_candidate_files_were_read(run)

    def _assert_dry_classifications_were_selected(
        self,
        run: PreservedLiveWorkflowRun,
    ) -> None:
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        classification_events = [
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("local_step_id") == "classify_candidate"
            and not event.get("empty_collection", False)
        ]
        empty_classifications = [
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("local_step_id") == "classify_candidate"
            and event.get("empty_collection", False)
        ]

        self.assertTrue(classification_events)
        self.assertTrue(all(
            event.get("item") is None
            and event.get("outputs", {}).get("assessment") == []
            for event in empty_classifications
        ))
        for classification in classification_events:
            selected = any(
                selection["path"] == classification["item"]["path"]
                and selection["unit"] == classification["item"]["unit"]
                for event in events
                if event.get("event") == "step_completed"
                and event.get("local_step_id") == "select_candidates"
                and event.get("workflow_instance_id")
                == classification.get("parent_workflow_instance_id")
                for selection in event["outputs"]["selections"]
            )
            self.assertTrue(selected)

    def _assert_dry_candidate_files_were_read(
        self,
        run: PreservedLiveWorkflowRun,
    ) -> None:
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        classifications = [
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("local_step_id") == "classify_candidate"
            and not event.get("empty_collection", False)
        ]
        tool_inputs = self._custom_tool_inputs(self._transcript(run))

        for classification in classifications:
            candidate_path = str(classification["item"]["path"])
            classification_instance = str(classification["instance_id"])
            read_indexes = [
                index
                for index, tool_input in enumerate(tool_inputs)
                if candidate_path in tool_input and "flow_next" not in tool_input
            ]
            submission_indexes = [
                index
                for index, tool_input in enumerate(tool_inputs)
                if classification_instance in tool_input and "flow_next" in tool_input
            ]
            self.assertTrue(
                read_indexes,
                f"Selected DRY candidate was not read: {candidate_path}",
            )
            self.assertTrue(
                submission_indexes,
                f"DRY classification was not submitted: {classification_instance}",
            )
            self.assertLess(min(read_indexes), min(submission_indexes))

    @staticmethod
    def _custom_tool_inputs(transcript: Path) -> list[str]:
        inputs: list[str] = []
        for line in transcript.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            payload = event.get("payload", {})
            if payload.get("type") != "custom_tool_call":
                continue
            tool_input = payload.get("input")
            if isinstance(tool_input, str):
                inputs.append(tool_input)
        return inputs

    def _evidence(
        self,
        run: PreservedLiveWorkflowRun,
        elapsed_seconds: float,
    ) -> ReviewComparisonRunEvidence:
        events = [
            FlowAuditEvent.model_validate_json(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        workflow = run.run_directory / "workflow.yaml"
        transcript = self._transcript(run)
        usage = CodexTranscriptTokenUsageReader().read(transcript)
        return ReviewComparisonRunEvidence(
            approach="workflow-review",
            phase="smoke",
            iteration=0,
            model_profile=self.MODEL_PROFILE,
            model="gpt-5.6-terra",
            target_path=str(self._source_project.review_target),
            target_sha256=self._sha256(self._source_project.review_target),
            effective_instructions_sha256=self._sha256(workflow),
            active_rule_ids=sorted(
                {
                    expectation.workflow_id
                    for expectation in self.EXPECTED_RULE_RESULTS
                }
            ),
            review_stage=CodexReviewStageEvidenceReader().read(
                transcript=transcript,
                prompt_marker="Call mcp__pipeline__flow_start",
                completion_tool="flow_next",
                completion_marker="Flow complete.",
            ),
            full_run=ReviewComparisonStageEvidence(
                elapsed_seconds=elapsed_seconds,
                token_usage=usage,
            ),
            reported_cost_available=False,
            reported_cost_usd=0,
            retry_count=sum(
                event.event == "step_attempt_failed" for event in events
            ),
            error_count=sum(
                event.event in {"step_rejected", "run_failed"}
                for event in events
            ),
            completed=events[-1].event == "run_completed",
        )

    @staticmethod
    def _transcript(run: PreservedLiveWorkflowRun) -> Path:
        transcripts = sorted(
            (
                run.session.artifact_directory
                / "codex-runtime"
                / "sessions"
            ).rglob("*.jsonl")
        )
        if not transcripts:
            raise RuntimeError("Codex workflow session preserved no transcript")
        return transcripts[-1]

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
