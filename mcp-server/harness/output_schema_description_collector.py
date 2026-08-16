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
        if not outputs:
            return []
        response_schema = {
            "type": "object",
            "properties": {
                output.name: output.schema or {}
                for output in outputs
            },
            "required": [output.name for output in outputs],
            "additionalProperties": False,
        }
        return [
            "Return only one JSON object matching this schema. Do not wrap it in "
            "Markdown fences or include any other text: "
            f"{self._serializer.serialize(response_schema)}"
        ]
