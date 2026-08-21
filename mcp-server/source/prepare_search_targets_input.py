"""Defines deterministic source-search target preparation input."""

from pydantic import BaseModel, ConfigDict

from source.analyze_source_input import AnalysisSource
from source.search_target_granularity import SearchTargetGranularity


"""
solid-name: PrepareSearchTargetsInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Selects one sealed source input and file-or-unit search granularity.
"""
class PrepareSearchTargetsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: AnalysisSource
    granularity: SearchTargetGranularity
