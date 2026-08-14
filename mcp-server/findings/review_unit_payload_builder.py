"""Builds persisted payloads for typed review units."""

from findings.principle_metrics_payload_building import (
    PrincipleMetricsPayloadBuilding,
)
from findings.review_unit import ReviewUnit
from findings.review_unit_payload_building import ReviewUnitPayloadBuilding


"""
solid-name: ReviewUnitPayloadBuilder
solid-category: boundary-adapter
solid-description: Builds the persisted identity, measurements, and violations for one reviewed unit.
"""
class ReviewUnitPayloadBuilder(ReviewUnitPayloadBuilding):
    def __init__(self, metrics_builder: PrincipleMetricsPayloadBuilding) -> None:
        self._metrics_builder = metrics_builder

    def build(self, unit: ReviewUnit) -> dict:
        payload = {
            "unit_name": unit.name,
            "unit_kind": unit.kind.value,
            "metrics": {
                metrics.principle: self._metrics_builder.build(metrics)
                for metrics in unit.metrics
            },
            "violations": [
                {
                    "rule_id": violation.rule_id,
                    "severity": violation.severity.value,
                }
                for violation in unit.violations
            ],
        }
        if unit.line_start is not None:
            payload["line_start"] = unit.line_start
        if unit.line_end is not None:
            payload["line_end"] = unit.line_end
        return payload
