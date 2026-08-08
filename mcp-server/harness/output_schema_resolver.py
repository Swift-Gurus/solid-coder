"""Applies external schema content to workflow step outputs."""

from __future__ import annotations

from harness.output_collection_resolving import OutputCollectionResolving
from harness.output_schema_resolving import OutputSchemaResolving
from harness.step_declaring_file_resolving import StepDeclaringFileResolving


"""
solid-name: OutputSchemaResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Delegates declaring-file and output-collection resolution for one workflow step.
"""
class OutputSchemaResolver(OutputSchemaResolving):

    def __init__(
        self,
        declaring_file_resolver: StepDeclaringFileResolving,
        output_collection_resolver: OutputCollectionResolving,
    ) -> None:
        self._declaring_file_resolver = declaring_file_resolver
        self._output_collection_resolver = output_collection_resolver

    def resolve(self, step: dict, flow_file_path: str) -> dict:
        outputs = step.get("outputs")
        if not outputs:
            return step

        declaring_file = self._declaring_file_resolver.resolve(step, flow_file_path)
        resolved_outputs = self._output_collection_resolver.resolve(step, declaring_file)

        resolved = dict(step)
        resolved["outputs"] = resolved_outputs
        return resolved
