"""Creates workflow-step output specifications."""

from __future__ import annotations

from harness.output_spec import OutputSpec
from harness.output_spec_creating import OutputSpecCreating


"""
solid-name: OutputSpecFactory
solid-category: factory
solid-spec: [SPEC-030]
solid-description: Creates immutable workflow-step output specifications.
"""
class OutputSpecFactory(OutputSpecCreating):
    def create(
        self,
        name: str,
        output_type: str,
        schema: dict | None,
        schema_file: str | None,
    ) -> OutputSpec:
        return OutputSpec(
            name=name,
            type=output_type,
            schema=schema,
            schema_file=schema_file,
        )
