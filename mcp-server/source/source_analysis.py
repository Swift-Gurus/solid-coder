"""Defines the typed result of deterministic source analysis."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_analysis_decision import SourceAnalysisDecision
from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit
from source.technology_detection import TechnologyDetection


"""
solid-name: SourceAnalysis
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries source identity, exact extension, parse outcome, recoverable diagnostics, ordered units, and tag evidence.
"""
class SourceAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_identity: str = Field(min_length=1)
    file_extension: str
    decision: SourceAnalysisDecision
    diagnostics: list[SourceParseDiagnostic] = Field(default_factory=list)
    units: list[SourceUnit] = Field(default_factory=list)
    detections: list[TechnologyDetection] = Field(default_factory=list)
