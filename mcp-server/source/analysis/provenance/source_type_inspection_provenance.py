"""Preserves separate binding roles for one source-local inspection."""

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.provenance.source_symbol_provenance import SourceSymbolProvenance
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection


"""
solid-name: SourceTypeInspectionProvenance
solid-category: model
solid-spec: [SPEC-064]
solid-description: Preserves inspection identity, value binding, value contract, destination ownership and unresolved evidence independently of rule classification.
"""
class SourceTypeInspectionProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inspection: SourceTypeInspection
    value: SourceSymbolProvenance
    contract: SourceSymbolProvenance
    destination: SourceSymbolProvenance
    verified: bool
    limitations: list[str] = Field(default_factory=list)
