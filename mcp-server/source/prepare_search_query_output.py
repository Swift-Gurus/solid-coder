"""Defines deterministic source-search query preparation output."""

from pydantic import BaseModel, ConfigDict

from source.source_search_query import SourceSearchQuery
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: PrepareSearchQueryOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Defines validated query and exclusion results for deterministic source search.
"""
class PrepareSearchQueryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    queries: list[SourceSearchQuery]
    excluded_units: list[SourceUnitIdentity]
