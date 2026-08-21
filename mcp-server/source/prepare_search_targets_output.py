"""Defines deterministic source-search target preparation output."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_search_target import SourceSearchTarget


"""
solid-name: PrepareSearchTargetsOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Returns ordered immutable search targets and reviewed-source exclusions.
"""
class PrepareSearchTargetsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    targets: list[SourceSearchTarget]
    excluded_source_identities: list[str] = Field(min_length=1)
