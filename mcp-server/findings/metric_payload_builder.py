"""Builds persisted payloads for typed metric measurements."""

from findings.metric_payload_building import MetricPayloadBuilding
from findings.metric_value import MetricValue


"""
solid-name: MetricPayloadBuilder
solid-category: boundary-adapter
solid-description: Builds the persisted value and audit context for one metric measurement.
"""
class MetricPayloadBuilder(MetricPayloadBuilding):
    def build(self, measurement: MetricValue) -> dict:
        return {
            "value": measurement.value,
            "is_exception": measurement.is_exception,
            "additional_info": {
                "reasoning": measurement.additional_info.reasoning,
                "evidence": measurement.additional_info.evidence,
            },
        }
