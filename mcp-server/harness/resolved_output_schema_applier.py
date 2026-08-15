"""Applies loaded schemas to output specifications."""

from harness.output_spec import OutputSpec
from harness.resolved_output_schema_applying import ResolvedOutputSchemaApplying


"""
solid-name: ResolvedOutputSchemaApplier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Applies a loaded JSON schema to an output specification.
"""
class ResolvedOutputSchemaApplier(ResolvedOutputSchemaApplying):
    def apply(self, output: OutputSpec, schema: dict) -> OutputSpec:
        return OutputSpec(
            name=output.name,
            type=output.type,
            schema=schema,
            schema_file=None,
        )
