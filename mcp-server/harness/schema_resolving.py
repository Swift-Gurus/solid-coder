"""
solid-description: Resolves JSON Schemas from OutputSpecs.
solid-category: service
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from scoring.yaml_config_file_loader import ConfigFileLoading
from harness.models import OutputSpec


class SchemaResolving(Protocol):
    """
    solid-description: Contract for resolving a JSON Schema from an OutputSpec.
    solid-category: abstraction
    """

    def resolve(self, output_spec: OutputSpec) -> dict | None: ...


class SchemaResolver:
    """
    solid-description: Resolves a JSON Schema from an OutputSpec.
    solid-category: service
    """

    def __init__(self, file_loader: ConfigFileLoading) -> None:
        self._file_loader = file_loader

    def resolve(self, output_spec: OutputSpec) -> dict | None:
        if output_spec.schema is not None:
            return output_spec.schema
        if output_spec.schema_file:
            return self._file_loader.load(Path(output_spec.schema_file))
        return None
