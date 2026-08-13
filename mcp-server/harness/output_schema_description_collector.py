"""Collects workflow output-schema requirements."""

from __future__ import annotations

from harness.output_schema_description_collecting import OutputSchemaDescriptionCollecting
from harness.output_spec import OutputSpec
from json_serializer import JsonSerializing


"""
solid-name: OutputSchemaDescriptionCollector
solid-category: service
solid-spec: [SPEC-027]
solid-description: Describes schema requirements for workflow-step outputs that declare schemas.
"""
class OutputSchemaDescriptionCollector(OutputSchemaDescriptionCollecting):
    def __init__(self, serializer: JsonSerializing) -> None:
        self._serializer = serializer

    def collect(self, outputs: list[OutputSpec]) -> list[str]:
        return [
            f"Submit output '{output.name}' matching this schema: "
            f"{self._serializer.serialize(output.schema)}"
            for output in outputs
            if output.schema is not None
        ]
