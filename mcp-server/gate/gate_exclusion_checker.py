"""
solid-description: Checks whether a file path is excluded from pre_write_gate health checks.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Protocol

from gate.exclusion_checking import ExclusionChecking
from utils.patterns.fnmatch_pattern_matcher import PatternMatching


"""
solid-name: ExclusionPatternResolving
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for identifying the configured path exclusion that explains an eligibility decision.
"""
class ExclusionPatternResolving(Protocol):
    def matched_pattern(self, file_path: str) -> str | None: ...


"""
solid-name: GateExclusionChecker
solid-category: service
solid-spec: [SPEC-064]
solid-description: Applies configured path exclusions and preserves the matching pattern for gate, search and ownership audit decisions.
"""
class GateExclusionChecker(ExclusionChecking, ExclusionPatternResolving):

    def __init__(
        self,
        patterns: list[str],
        matcher: PatternMatching,
    ) -> None:
        self._patterns = list(patterns)
        self._matcher = matcher

    def is_excluded(self, file_path: str) -> bool:
        return self.matched_pattern(file_path) is not None

    def matched_pattern(self, file_path: str) -> str | None:
        return next((pattern for pattern in self._patterns if self._matcher.matches(file_path, pattern)), None)
