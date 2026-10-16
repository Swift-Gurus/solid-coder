from pydantic import BaseModel, ConfigDict, Field

from source.source_analysis import SourceAnalysis


"""
solid-name: SourceCandidateAnalyses
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves inspected candidate snapshots and explicit evidence limitations for downstream declaration analysis.
"""
class SourceCandidateAnalyses(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analyses: list[SourceAnalysis] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
