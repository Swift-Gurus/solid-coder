"""Clears expanded co-located metrics from their owner step."""

from harness.co_located_metrics_clearing import CoLocatedMetricsClearing
from harness.co_located_metrics_replacing import CoLocatedMetricsReplacing
from harness.step_declaration import StepDeclaration

"""
solid-name: CoLocatedMetricsClearer
solid-category: service
solid-spec: [SPEC-058]
solid-description: Removes co-located metric contracts after expanding them into ordinary metric steps.
"""


class CoLocatedMetricsClearer(CoLocatedMetricsClearing):
    def __init__(
        self,
        metrics_replacer: CoLocatedMetricsReplacing,
    ) -> None:
        self._metrics_replacer = metrics_replacer

    def clear(self, owner: StepDeclaration) -> StepDeclaration:
        return self._metrics_replacer.replace_metrics(owner, [])
