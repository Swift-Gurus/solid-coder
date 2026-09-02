"""Defines backend-neutral live assertions for the one-call SRP experiment."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import BaseModel

_HARNESS_DIRECTORY = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
for _directory in (_HARNESS_DIRECTORY, _MCP_SERVER):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from flow_audit_event import FlowAuditEvent  # noqa: E402
from harness.step_completed_event import StepCompletedEvent  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_workflow_e2e_live_base import LiveWorkflowE2ELiveBase  # noqa: E402
from live_workflow_scenario import LiveWorkflowScenario  # noqa: E402
from preserved_live_workflow_run import PreservedLiveWorkflowRun  # noqa: E402
from review_unit_workflow_context import ReviewUnitWorkflowContext  # noqa: E402
from review_unit_workflow_parameters import ReviewUnitWorkflowParameters  # noqa: E402
from review_unit_workflow_target import ReviewUnitWorkflowTarget  # noqa: E402
from srp_single_prompt_output import SRPSinglePromptOutput  # noqa: E402


_PROJECT_ROOT = _MCP_SERVER.parent
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "SRP" / "fixtures" / "fixture-1.swift"


"""
solid-name: SRPSinglePromptValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-036]
solid-description: Applies one backend-neutral live contract to the schema-validated single-prompt SRP comparison workflow.
"""
class SRPSinglePromptValidationE2ELiveBase(LiveWorkflowE2ELiveBase):
    PROJECT_ROOT = _PROJECT_ROOT

    @property
    def workflow_parameters(self) -> BaseModel:
        return ReviewUnitWorkflowParameters(
            review_unit=ReviewUnitWorkflowContext(
                target=ReviewUnitWorkflowTarget(name=_FIXTURE.name)
            ),
        )

    @property
    def scenario(self) -> LiveWorkflowScenario:
        return LiveWorkflowScenario(
            workflow_id="srp-single-prompt",
            parameters=self.workflow_parameters,
            artifact_scope=LiveSessionArtifactScope(
                domain="comparison",
                scenario="workflow-srp-single-prompt",
            ),
            model_context=(
                "Source under review:\n"
                "```swift\n"
                f"{_FIXTURE.read_text(encoding='utf-8')}"
                "\n```"
            ),
        )

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        lines = [
            line
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        events = [FlowAuditEvent.model_validate_json(line) for line in lines]
        self.assertEqual(events[-1].event, "run_completed")
        self.assertFalse(
            {event.event for event in events}
            & {"step_attempt_failed", "step_rejected", "run_failed"}
        )
        completed_steps = [
            StepCompletedEvent.model_validate_json(line)
            for line, event in zip(lines, events)
            if event.event == "step_completed"
        ]
        self.assertEqual(len(completed_steps), 1)
        completed = completed_steps[0]
        self.assertEqual(completed.step_id, "assess_srp")
        output = SRPSinglePromptOutput.model_validate(completed.outputs)
        self.assertEqual(output.verb_count.value, 6)
        self.assertEqual(output.cohesion_groups.value, 2)
        self.assertEqual(output.stakeholder_count.value, 2)
        self.assertFalse(output.exception.is_exception)
        for measurement in (
            output.verb_count,
            output.cohesion_groups,
            output.stakeholder_count,
        ):
            self.assertTrue(measurement.additional_info.reasoning)
            self.assertTrue(measurement.additional_info.evidence)
        self.assertTrue(output.exception.additional_info.reasoning)
        self.assertTrue(output.exception.additional_info.evidence)
