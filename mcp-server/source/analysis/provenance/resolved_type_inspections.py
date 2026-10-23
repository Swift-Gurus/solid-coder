"""Carries ordered semantic evidence and inventory completeness."""

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.provenance.source_type_inspection_provenance import (
    SourceTypeInspectionProvenance,
)

"""
solid-name: ResolvedTypeInspections
solid-category: model
solid-spec: [SPEC-064]
solid-description: Preserves ordered type inspections and inventory limitations without turning missing evidence into measured compliance.
"""


class ResolvedTypeInspections(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inspections: list[SourceTypeInspectionProvenance] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    context: str = ""
