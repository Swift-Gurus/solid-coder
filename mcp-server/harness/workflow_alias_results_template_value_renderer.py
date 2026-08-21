"""Renders workflow-alias results as JSON template values."""

from __future__ import annotations

from typing import cast

from harness.template_value_rendering import TemplateValueRendering
from harness.workflow_alias_results import WorkflowAliasResults
from harness.workflow_result_envelope_serializing import (
    WorkflowResultEnvelopeSerializing,
)
from json_serializer import JsonSerializing


"""
solid-name: WorkflowAliasResultsTemplateValueRenderer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Renders ordered workflow-alias results as canonical JSON template text.
"""
class WorkflowAliasResultsTemplateValueRenderer(TemplateValueRendering):

    def __init__(
        self,
        envelope_serializer: WorkflowResultEnvelopeSerializing,
        json_serializer: JsonSerializing,
    ) -> None:
        self._envelope_serializer = envelope_serializer
        self._json_serializer = json_serializer

    def render(self, value: object) -> str:
        results = cast(WorkflowAliasResults, value)
        return self._json_serializer.serialize([
            self._envelope_serializer.serialize(envelope)
            for envelope in results.entries
        ])
