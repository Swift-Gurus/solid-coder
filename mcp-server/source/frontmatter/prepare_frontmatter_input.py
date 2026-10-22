"""Input boundary for declaration-backed metadata validation."""

from pydantic import BaseModel, ConfigDict

from source.source_analysis import SourceAnalysis


"""
solid-name: PrepareFrontmatterInput
solid-category: model
solid-spec: [SPEC-069]
solid-description: Carries the exact source analysis whose declaration metadata will be inspected.
"""
class PrepareFrontmatterInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis: SourceAnalysis
