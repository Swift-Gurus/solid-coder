"""Defines deterministic source-search target preparation output."""

from pydantic import BaseModel, ConfigDict

from source.source_search_target import SourceSearchTarget
from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: PrepareSearchTargetsOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Returns ordered immutable search targets and reviewed-source exclusions.
"""
class PrepareSearchTargetsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    targets: list[SourceSearchTarget]
    snapshot: RepositorySourceSnapshot
