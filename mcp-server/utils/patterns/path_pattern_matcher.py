"""Matches configured path globs without losing recursive-pattern suffixes."""

from utils.patterns.fnmatch_pattern_matcher import PatternMatching


"""
solid-name: PathPatternMatcher
solid-category: utility
solid-spec: [SPEC-064]
solid-description: Matches path segments against glob patterns while preserving recursive wildcards, suffix constraints and absolute anchors.
"""
class PathPatternMatcher(PatternMatching):
    def __init__(self, segments: PatternMatching) -> None:
        self._segments = segments

    def matches(self, text: str, pattern: str) -> bool:
        normalized = text.replace("\\", "/")
        normalized_pattern = pattern.replace("\\", "/")
        if not normalized_pattern:
            return False
        path_parts = normalized.split("/")
        pattern_parts = normalized_pattern.split("/")
        positions = {0} if normalized_pattern.startswith("/") else set(range(len(path_parts)))
        for part in pattern_parts:
            if part == "**":
                positions = set(range(min(positions), len(path_parts) + 1)) if positions else set()
            else:
                positions = {
                    position + 1
                    for position in positions
                    if position < len(path_parts) and self._segments.matches(path_parts[position], part)
                }
        return len(path_parts) in positions
