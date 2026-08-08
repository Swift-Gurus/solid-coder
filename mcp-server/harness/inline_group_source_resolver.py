"""Resolves one inline workflow group."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_source import IncludeSource
from harness.include_source_creating import IncludeSourceCreating
from harness.step_source_annotating import StepSourceAnnotating


"""
solid-name: InlineGroupSourceResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Selects and annotates the non-empty steps declared by one inline workflow group.
"""
class InlineGroupSourceResolver:

    def __init__(
        self,
        source_annotator: StepSourceAnnotating,
        error_factory: FlowValidationErrorCreating,
        source_factory: IncludeSourceCreating,
    ) -> None:
        self._source_annotator = source_annotator
        self._error_factory = error_factory
        self._source_factory = source_factory

    def resolve(self, entry: dict, flow_file_path: str, search_paths: list[str]) -> IncludeSource | None:
        alias = entry.get("group")
        if alias is None:
            return None
        steps = entry.get("steps") or []
        if not steps:
            raise self._error_factory.create(
                f"Group '{alias}' must declare a non-empty 'steps' list"
            )
        source_path = entry.get("__source_file") or flow_file_path
        return self._source_factory.create(
            alias=alias,
            steps=self._source_annotator.annotate(steps, source_path),
            flow_path=source_path,
        )
