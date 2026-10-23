"""Defines codebase-search term resolution."""

from pathlib import Path
from typing import Protocol

from search.codebase_search_terms import CodebaseSearchTerms

"""
solid-name: CodebaseSearchTermsResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving direct and plan-derived source-search terms.
"""


class CodebaseSearchTermsResolving(Protocol):
    def resolve(
        self,
        plan_path: Path | None,
        tags: list[str] | None,
        spec_numbers: list[str] | None,
    ) -> CodebaseSearchTerms: ...
