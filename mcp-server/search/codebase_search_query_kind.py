"""Defines query identities used by the codebase-search compatibility boundary."""

from enum import Enum


"""
solid-name: CodebaseSearchQueryKind
solid-category: model
solid-spec: [SPEC-040]
solid-description: Identifies direct-term and specification queries in codebase source search.
"""
class CodebaseSearchQueryKind(str, Enum):
    TERMS = "terms"
    SPECIFICATIONS = "specifications"
