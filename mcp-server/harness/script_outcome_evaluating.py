"""
solid-name: ScriptOutcomeEvaluating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for evaluating script execution results into step outcomes.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef
from harness.script_execution_result import ScriptExecutionResult
from harness.step_run_outcome import StepRunOutcome


class ScriptOutcomeEvaluating(Protocol):

    def evaluate(self, result: ScriptExecutionResult, step: StepDef) -> StepRunOutcome: ...