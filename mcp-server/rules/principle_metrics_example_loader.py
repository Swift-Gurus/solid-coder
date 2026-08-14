"""Loads principle metric examples from review schemas."""

from pathlib import Path

from health.llama.json_deserializer import JsonDeserializing
from rules.metric_submission_example_building import MetricSubmissionExampleBuilding
from rules.principle_metrics_example_loading import PrincipleMetricsExampleLoading
from utils.prompt_builder import TextFileReading


"""
solid-name: PrincipleMetricsExampleLoader
solid-category: service
solid-description: Reads one principle review schema and produces its complete set of auditable metric submission examples.
"""
class PrincipleMetricsExampleLoader(PrincipleMetricsExampleLoading):
    def __init__(
        self,
        reader: TextFileReading,
        deserializer: JsonDeserializing,
        example_builder: MetricSubmissionExampleBuilding,
    ) -> None:
        self._reader = reader
        self._deserializer = deserializer
        self._example_builder = example_builder

    def load(self, schema_path: Path) -> dict:
        content = self._reader.read(schema_path)
        if content is None:
            return {}
        schema = self._deserializer.deserialize(content.encode("utf-8"))
        if schema is None:
            return {}
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        return {
            variable_name: self._example_builder.build(
                properties.get(variable_name, {})
            )
            for variable_name in required
        }
