"""Coordinates source-health validation through the executable flow engine."""

from typing import Optional

from gate_flow_prompt_building import GateFlowPromptBuilding
from gate_review_input_building import GateReviewInputBuilding
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_run_orchestrating import FlowRunOrchestrating
from health_violation import HealthViolation
from llm.claude_runner import ClaudeRunning
from patch_review_context import PatchReviewContext
from review_result_reading import ReviewResultReading
from review_violation_selecting import ReviewViolationSelecting


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
        violation_selector: ReviewViolationSelecting,
        input_builder: GateReviewInputBuilding,
        prompt_builder: GateFlowPromptBuilding,
        timeout_seconds: int,
    ) -> None:
        self._flow = flow
        self._renderer = renderer
        self._runner = runner
        self._result_reader = result_reader
        self._violation_selector = violation_selector
        self._input_builder = input_builder
        self._prompt_builder = prompt_builder
        self._timeout_seconds = timeout_seconds

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
        patch_context: Optional[PatchReviewContext] = None,
        principle_names: Optional[list[str]] = None,
    ) -> list[HealthViolation]:
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
            return []

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
        if not response:
            raise RuntimeError("Gate workflow child session returned no result")

        status = self._flow.flow_status(started.run_id)
        if status.status != "done":
            detail = status.error or status.status
            raise RuntimeError(
                f"Gate workflow did not complete: {detail}"
            )
        return self._violation_selector.select(
            self._result_reader.read(started.run_id)
        )
