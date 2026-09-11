"""Serializes one resolved workflow output specification."""

from harness.output_spec import OutputSpec
from harness.output_spec_schema_serializing import OutputSpecSchemaSerializing


"""
solid-name: OutputSpecSchemaSerializer
solid-category: service
solid-spec: [SPEC-045]
solid-description: Produces the declared JSON Schema or the output type fallback for one workflow output.
"""
class OutputSpecSchemaSerializer(OutputSpecSchemaSerializing):
    def serialize(self, output: OutputSpec) -> dict[str, object]:
        if output.schema is not None:
            return output.schema
        if output.type == "data":
            return {}
        if output.type == "file":
            return {"type": "string"}
        return {"type": output.type}
