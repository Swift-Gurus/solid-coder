from pydantic import BaseModel, ConfigDict

from harness.collection_ratio_observation import CollectionRatioObservation
from source.analysis.matching.source_requirement_match import SourceRequirementMatch


"""
solid-name: ValidateRequirementCoverageInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Associates authoritative requirement matches with candidate availability and submitted coverage observations.
"""
class ValidateRequirementCoverageInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    matches: list[SourceRequirementMatch]
    availability: CollectionRatioObservation
    coverage_entries: list[CollectionRatioObservation]
