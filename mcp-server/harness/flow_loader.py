"""Loads and coordinates validation of workflow definitions."""

from pathlib import Path

from harness.flow_definition_assembling import FlowDefinitionAssembling
from harness.flow_definition_resolving import FlowDefinitionResolving
from harness.flow_definition_validating import FlowDefinitionValidating
from harness.flow_def import FlowDef
from harness.flow_loading import FlowLoading
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from scoring.yaml_config_file_loader import ConfigFileLoading


"""
solid-name: FlowLoader
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Loads and validates flow definitions through injected resolution, validation, and assembly capabilities.
"""
class FlowLoader(FlowLoading):

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        definition_resolver: FlowDefinitionResolving,
        definition_validator: FlowDefinitionValidating,
        definition_assembler: FlowDefinitionAssembling,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._file_loader = file_loader
        self._definition_resolver = definition_resolver
        self._definition_validator = definition_validator
        self._definition_assembler = definition_assembler
        self._error_factory = error_factory

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        raw = self._file_loader.load(Path(path))
        if raw is None:
            raise self._error_factory.create(f"Flow file not found or unreadable: '{path}'")
        resolved = self._definition_resolver.resolve(raw, path, search_paths)
        self._definition_validator.validate_resolved(resolved)
        flow = self._definition_assembler.assemble(resolved)
        self._definition_validator.validate_assembled(flow)
        return flow
