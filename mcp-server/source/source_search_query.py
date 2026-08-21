"""Defines one typed repository source-search query."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SearchQueryIdentity = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
SearchTerm = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        pattern=r"^[^\s,;]+$",
    ),
]


"""
solid-name: SourceSearchQuery
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries a stable query identity and explicit normalized search terms.
"""
class SourceSearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: SearchQueryIdentity
    terms: Annotated[list[SearchTerm], Field(min_length=1)]
