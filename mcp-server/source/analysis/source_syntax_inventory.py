"""Typed facts crossing the language-parser boundary."""

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.calls.source_call import SourceCall
from source.analysis.declarations.source_scoped_declaration import SourceScopedDeclaration
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.source_evidence import SourceEvidence
from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit


"""
solid-name: SourceSyntaxInventory
solid-category: model
solid-spec: [SPEC-057, SPEC-063]
solid-description: Records declarations, imports, syntax evidence, type inspections and recoverable diagnostics for deterministic source analysis.
"""
class SourceSyntaxInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    units: list[SourceUnit] = Field(default_factory=list)
    declarations: list[SourceScopedDeclaration] = Field(default_factory=list)
    imports: list[SourceEvidence] = Field(default_factory=list)
    signals: list[SourceEvidence] = Field(default_factory=list)
    calls: list[SourceCall] = Field(default_factory=list)
    type_inspections: list[SourceTypeInspection] = Field(default_factory=list)
    diagnostics: list[SourceParseDiagnostic] = Field(default_factory=list)
