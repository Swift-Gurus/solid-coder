"""Selects a prepared review target within its authoritative source snapshot."""

from pydantic import BaseModel, ConfigDict
from source.source_search_context import SourceSearchContext
from source.source_search_target import SourceSearchTarget

"""
solid-name: ResolveTypeInspectionsInput
solid-category: model
solid-spec: [SPEC-064]
solid-description: Selects the reviewed declaration and prospective source context for semantic type-inspection preparation without model-supplied ownership or project paths.
"""


class ResolveTypeInspectionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: SourceSearchTarget
    context: SourceSearchContext
    file_extension: str
