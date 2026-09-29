"""Adapts dataclass replacement to co-located metric metadata."""

from dataclasses import replace

from harness.co_located_metric_contract import CoLocatedMetricContract
from harness.co_located_metrics_replacing import CoLocatedMetricsReplacing
from harness.step_declaration import StepDeclaration


"""
solid-name: DataclassCoLocatedMetricsReplacer
solid-category: adapter
solid-spec: [SPEC-058]
solid-description: Replaces compact metric metadata while preserving all other workflow-step fields.
"""
class DataclassCoLocatedMetricsReplacer(CoLocatedMetricsReplacing):
    def replace_metrics(
        self,
        step: StepDeclaration,
        metrics: list[CoLocatedMetricContract],
    ) -> StepDeclaration:
        return replace(step, co_located_metrics=metrics)
