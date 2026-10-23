"""Defines one fully decoded compact metric awaiting step expansion."""

from dataclasses import dataclass

from harness.metric_step_contract import MetricStepContract

"""
solid-name: CoLocatedMetricContract
solid-category: model
solid-spec: [SPEC-058]
solid-description: Represents a decoded co-located measurement with stable identity and deterministic scoring metadata.
"""


@dataclass(frozen=True)
class CoLocatedMetricContract:
    id: str
    step_contract: MetricStepContract
