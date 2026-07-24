"""
solid-name: DelegateStepHandler
solid-category: service
solid-spec: [SPEC-027]
solid-description: Routes delegate steps to appropriate handlers based on their configured mode.
"""

from __future__ import annotations

from harness.delegate_instruction_building import build_delegate_instruction
from harness.models import FlowDef, StepDef, StepInstance, ValidationResult
from harness.session_delegate_running import SessionDelegateRunning
from harness.step_handling import StepHandling
from harness.step_run_outcome import StepRunOutcome

_SESSION_MODE = "session"


class DelegateStepHandler(StepHandling):

    def __init__(self, agent_handler: StepHandling, session_runner: SessionDelegateRunning) -> None:
        self._agent_handler = agent_handler
        self._session_runner = session_runner

    def run(self, step_instance: StepInstance, step_def: StepDef) -> StepRunOutcome:
        if step_def.mode == _SESSION_MODE:
            return self._session_runner.run(build_delegate_instruction(step_instance.prompt))
        return self._agent_handler.run(step_instance, step_def)

    def validate(self, step_instance: StepInstance, outputs: dict, flow_def: FlowDef) -> ValidationResult:
        return self._agent_handler.validate(step_instance, outputs, flow_def)
