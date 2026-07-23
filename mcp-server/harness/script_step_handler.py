"""
solid-name: ScriptStepHandler
solid-category: service
solid-spec: [SPEC-027]
solid-description: Executes script-type steps and evaluates their outcomes against declared schemas.
"""

from __future__ import annotations

from harness.models import FlowDef, StepDef, StepInstance, ValidationResult
from harness.script_outcome_evaluating import ScriptOutcomeEvaluating
from harness.step_handling import StepHandling
from harness.step_run_outcome import StepRunOutcome
from script_command_running import ScriptCommandRunning


class ScriptStepHandler(StepHandling):

    def __init__(self, runner: ScriptCommandRunning, evaluator: ScriptOutcomeEvaluating) -> None:
        self._runner = runner
        self._evaluator = evaluator

    def run(self, step_instance: StepInstance, step_def: StepDef) -> StepRunOutcome:
        result = self._runner.run(step_def.command, step_def.timeout_seconds)
        return self._evaluator.evaluate(result, step_def)

    def validate(self, step_instance: StepInstance, outputs: dict, flow_def: FlowDef) -> ValidationResult:
        return ValidationResult(ok=True)
