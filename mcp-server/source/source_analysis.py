"""Defines the typed result of deterministic source analysis."""

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.calls.source_call import SourceCall
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_evidence import SourceEvidence
from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit
from source.technology_detection import TechnologyDetection

"""
solid-name: SourceAnalysis
solid-category: model
solid-spec: [SPEC-040, SPEC-063]
solid-description: Records source identity, parse completeness, ordered declarations, type-inspection facts, technology evidence and recoverable diagnostics.
"""


class SourceAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_identity: str = Field(min_length=1)
    file_extension: str
    decision: SourceAnalysisDecision
    diagnostics: list[SourceParseDiagnostic] = Field(default_factory=list)
    units: list[SourceUnit] = Field(default_factory=list)
    declarations: list[SourceScopedDeclaration] = Field(default_factory=list)
    imports: list[SourceEvidence] = Field(default_factory=list)
    type_inspections: list[SourceTypeInspection] = Field(default_factory=list)
    calls: list[SourceCall] = Field(default_factory=list)
    detections: list[TechnologyDetection] = Field(default_factory=list)
