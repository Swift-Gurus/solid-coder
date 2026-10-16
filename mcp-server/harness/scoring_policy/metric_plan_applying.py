from typing import Protocol, TypeVar

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry

ScoredValue = TypeVar("ScoredValue")


"""
solid-name: MetricPlanApplying
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-057]
solid-description: Contract for applying resolved metric plans to a typed executable value while preserving its non-scoring metadata.
"""
class MetricPlanApplying(Protocol[ScoredValue]):
    def apply(self, value: ScoredValue, plans: list[EffectiveMetricPlanEntry]) -> ScoredValue: ...
