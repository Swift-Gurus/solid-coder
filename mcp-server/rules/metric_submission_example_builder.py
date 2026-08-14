"""Builds one auditable metric submission example."""

from rules.metric_submission_example_building import MetricSubmissionExampleBuilding
from rules.schema_minimal_value_resolving import SchemaMinimalValueResolving


"""
solid-name: MetricSubmissionExampleBuilder
solid-category: service
solid-description: Produces a schema-derived metric example containing its value, exception decision, reasoning, and source evidence.
"""
class MetricSubmissionExampleBuilder(MetricSubmissionExampleBuilding):
    def __init__(self, value_resolver: SchemaMinimalValueResolving) -> None:
        self._value_resolver = value_resolver

    def build(self, measurement_schema: dict) -> dict:
        value_schema = measurement_schema.get("properties", {}).get("value", {})
        return {
            "value": self._value_resolver.resolve(value_schema),
            "is_exception": False,
            "additional_info": {
                "reasoning": "Explain why the measured value and exception classification are correct.",
                "evidence": "Cite the relevant source line, excerpt, or precise code observation.",
            },
        }
