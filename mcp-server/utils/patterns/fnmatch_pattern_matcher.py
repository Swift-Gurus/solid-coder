"""Adapts standard-library glob comparison to the shared matching contract."""

import fnmatch
from typing import Protocol


"""
solid-name: PatternMatching
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for comparing text with a wildcard pattern.
"""
class PatternMatching(Protocol):
    def matches(self, text: str, pattern: str) -> bool: ...


"""
solid-name: FnmatchPatternMatcher
solid-category: adapter
solid-spec: [SPEC-064]
solid-description: Adapts case-sensitive wildcard comparison without adding path or ownership policy.
"""
class FnmatchPatternMatcher(PatternMatching):
    def matches(self, text: str, pattern: str) -> bool:
        return fnmatch.fnmatchcase(text, pattern)
