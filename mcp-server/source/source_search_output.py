"""Defines typed repository source-search output."""

from pydantic import Field
from source.source_search_results import SourceSearchResults

"""
solid-name: SourceSearchOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Reports source-search candidates, scanned files, and documented-file totals for audit summaries.
"""


class SourceSearchOutput(SourceSearchResults):
    files_with_frontmatter: int = Field(ge=0)
