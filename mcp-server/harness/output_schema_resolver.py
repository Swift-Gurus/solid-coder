"""Applies external schema content to workflow step outputs."""

from __future__ import annotations

from harness.output_collection_resolving import OutputCollectionResolving
from harness.output_schema_resolving import OutputSchemaResolving
from harness.resolved_outputs_applying import ResolvedOutputsApplying
from harness.step_declaring_file_resolving import StepDeclaringFileResolving
from harness.step_declaration import StepDeclaration


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
        outputs_applier: ResolvedOutputsApplying,
    ) -> None:
        self._declaring_file_resolver = declaring_file_resolver
        self._output_collection_resolver = output_collection_resolver
        self._outputs_applier = outputs_applier

    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
    ) -> StepDeclaration:
        if not step.outputs:
            return step

        declaring_file = self._declaring_file_resolver.resolve(
            step.source_file,
            flow_file_path,
        )
        resolved_outputs = self._output_collection_resolver.resolve(step, declaring_file)
        return self._outputs_applier.apply(step, resolved_outputs)
