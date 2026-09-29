"""Defines immutable co-located metric replacement on a workflow step."""

from typing import Protocol

from harness.co_located_metric_contract import CoLocatedMetricContract
from harness.step_declaration import StepDeclaration


"""
solid-name: CoLocatedMetricsReplacing
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for replacing compact metric metadata while preserving the remaining step declaration.
"""
class CoLocatedMetricsReplacing(Protocol):
    def replace_metrics(
        self,
        step: StepDeclaration,
        metrics: list[CoLocatedMetricContract],
    ) -> StepDeclaration: ...
