"""Coordinates source-health validation through the executable flow engine."""

from gate_flow_prompt_building import GateFlowPromptBuilding
from gate_review_input_building import GateReviewInputBuilding
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.operation_handling import OperationHandling
from health_check_outcome import HealthCheckOutcome
from health_review_assessor import HealthReviewAssessing
from llm.claude_runner import ClaudeRunning
from logging_protocol import Logging
from patch_review_context import PatchReviewContext
from review_result_reading import ReviewResultReading
from source.analysis.operations.source_introduction_evidence import (
    SourceIntroductionEvidence,
)
from source.text_analysis_source import TextAnalysisSource

_WORKFLOW_ID = "solid-gate-on-write"


"""
solid-name: WorkflowHealthChecker
solid-category: service
solid-spec: [SPEC-036, SPEC-039, SPEC-041]
solid-description: Coordinates one prospective source review through a server-started executable workflow.
"""


class WorkflowHealthChecker:
    def __init__(
        self,
        flow: FlowRunOrchestrating,
        renderer: FlowResultRendering,
        runner: ClaudeRunning,
        result_reader: ReviewResultReading,
        assessor: HealthReviewAssessing,
        introductions: OperationHandling[
            TextAnalysisSource, SourceIntroductionEvidence
        ],
        logger: Logging,
        input_builder: GateReviewInputBuilding,
        prompt_builder: GateFlowPromptBuilding,
        timeout_seconds: int,
    ) -> None:
        self._flow = flow
        self._renderer = renderer
        self._runner = runner
        self._result_reader = result_reader
        self._assessor = assessor
        self._introductions = introductions
        self._logger = logger
        self._input_builder = input_builder
        self._prompt_builder = prompt_builder
        self._timeout_seconds = timeout_seconds

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
        patch_context: PatchReviewContext | None = None,
        principle_names: list[str] | None = None,
    ) -> HealthCheckOutcome:
        introductions = self._introductions.execute(
            TextAnalysisSource(text=content, virtual_path=path)
        )
        review_input = self._input_builder.build(
            content,
            path,
            patch_context,
        )
        started = self._flow.flow_start(
            _WORKFLOW_ID,
            params=review_input.model_dump(mode="json"),
            isolated=True,
        )
        if started.error:
            raise RuntimeError(started.error)
        if not started.run_id:
            raise RuntimeError("Gate workflow did not return a run ID")
        if started.status == "done":
            return HealthCheckOutcome(introduction_evidence=introductions)

        response = None
        child_error = None
        try:
            response = self._runner.run(
                self._prompt_builder.build(
                    content=content,
                    path=path,
                    parent_session_id=parent_session_id,
                    run_id=started.run_id,
                    first_step=self._renderer.render_start(started),
                ),
                timeout=self._timeout_seconds,
            )
        except Exception as error:  # noqa: BLE001 — Retain child-session errors while checking authoritative workflow completion and reporting incomplete runs.
            child_error = error

        status = self._flow.flow_status(started.run_id)
        if status.status != "done":
            detail = status.error or status.status
            pending = ", ".join(status.pending) or "unknown"
            child_detail = (
                f"Child session error: {child_error}"
                if child_error is not None
                else f"Child session result: {response or 'no result'}"
            )
            raise RuntimeError(
                f"Gate workflow did not complete: {detail}\n"
                f"{child_detail}\n"
                f"Pending workflow steps: {pending}\n"
                "Retry the same write. The gate will start a new isolated review "
                "and resubmit the complete aggregate. Do not attempt a partial "
                "flow_next correction from the parent session or modify the source "
                "solely because of this infrastructure failure."
            )
        outcome = self._assessor.assess(
            self._result_reader.read(started.run_id),
            introductions,
        )
        self._logger.log(
            f"gate_review_outcome run_id={started.run_id} {outcome.model_dump_json()}"
        )
        return outcome
