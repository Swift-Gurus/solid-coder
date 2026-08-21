"""Defines auditable repository search match categories."""

from enum import Enum


"""
solid-name: SourceSearchMatchKind
solid-category: model
solid-spec: [SPEC-040]
solid-description: Identifies the deterministic source fact that matched a repository search term.
"""
class SourceSearchMatchKind(str, Enum):
    FILENAME = "filename"
    SYMBOL = "symbol"
    IMPORT = "import"
    FRONTMATTER = "frontmatter"
    CONTENT = "content"
