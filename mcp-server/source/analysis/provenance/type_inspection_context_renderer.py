"""Presents compact, verified inspection facts without internal provenance."""

from harness.template_value_rendering import TemplateValueRendering
from source.analysis.provenance.source_type_inspection_provenance import (
    SourceTypeInspectionProvenance,
)

"""
solid-name: TypeInspectionContextRenderer
solid-category: service
solid-spec: [SPEC-064]
solid-description: Renders verified inspection expressions and role ownership for model classification without repeating source or internal semantic identifiers.
"""


class TypeInspectionContextRenderer(
    TemplateValueRendering[list[SourceTypeInspectionProvenance]]
):
    def render(self, value: list[SourceTypeInspectionProvenance]) -> str:
        return "\n\n".join(
            f"Inspection: {fact.inspection.identity}\n"
            f"Expression (line {fact.inspection.span.start}): {fact.inspection.expression}\n"
            f"Value: {fact.value.ownership.value}; Contract: {fact.contract.ownership.value}; "
            f"Destination: {fact.destination.ownership.value}"
            for fact in value
            if fact.verified
        )
