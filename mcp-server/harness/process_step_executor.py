"""Executes process-backed workflow steps."""

from harness.models import StepDef, StepInstance
from harness.process_execution_running import ProcessExecutionRunning
from harness.script_outcome_evaluating import ScriptOutcomeEvaluating
from harness.step_process_execution_resolving import StepProcessExecutionResolving
from harness.step_run_outcome import StepRunOutcome


"""
solid-name: ProcessStepExecutor
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Executes typed workflow process requests and evaluates their declared outcomes.
"""
class ProcessStepExecutor:
    def __init__(
        self,
        execution_resolver: StepProcessExecutionResolving,
        runner: ProcessExecutionRunning,
        evaluator: ScriptOutcomeEvaluating,
    ) -> None:
        self._execution_resolver = execution_resolver
        self._runner = runner
        self._evaluator = evaluator

    def run(self, step_instance: StepInstance, step_def: StepDef) -> StepRunOutcome:
        execution = self._execution_resolver.resolve(step_def)
        result = self._runner.run(execution, step_def.timeout_seconds)
        return self._evaluator.evaluate(result, step_def)
