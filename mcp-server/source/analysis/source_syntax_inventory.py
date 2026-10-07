"""Typed facts crossing the language-parser boundary."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_evidence import SourceEvidence
from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit


"""
solid-name: SourceSyntaxInventory
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries parsed declarations, import and syntax evidence, and diagnostics without exposing parser nodes to consumers.
"""
class SourceSyntaxInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    units: list[SourceUnit] = Field(default_factory=list)
    imports: list[SourceEvidence] = Field(default_factory=list)
    signals: list[SourceEvidence] = Field(default_factory=list)
    diagnostics: list[SourceParseDiagnostic] = Field(default_factory=list)
