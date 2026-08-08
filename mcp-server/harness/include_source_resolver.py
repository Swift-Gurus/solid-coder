"""Routes an include entry to its supported source resolver."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_source import IncludeSource
from harness.include_source_resolving import IncludeSourceResolving


"""
solid-name: IncludeSourceResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Selects the first applicable workflow-ID, path, or inline-group source resolver.
"""
class IncludeSourceResolver:

    def __init__(
        self,
        resolvers: list[IncludeSourceResolving],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._resolvers = resolvers
        self._error_factory = error_factory

    def resolve(self, entry: dict, flow_file_path: str, search_paths: list[str]) -> IncludeSource | None:
        for resolver in self._resolvers:
            source = resolver.resolve(entry, flow_file_path, search_paths)
            if source is not None:
                return source
        if "include" in entry:
            raise self._error_factory.create(
                "Include must be a relative path or an object declaring 'workflow'"
            )
        return None
