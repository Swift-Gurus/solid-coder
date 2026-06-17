"""
solid-description: Checks whether a file path is excluded from pre_write_gate health checks.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Callable


class GateExclusionChecker:
    """Determines whether a file path matches any configured gate exclusion pattern."""

    def __init__(
        self,
        exclude_patterns_fn: Callable[[], list],
        path_matcher_fn: Callable[[str, str], bool],
    ) -> None:
        self._get_patterns = exclude_patterns_fn
        self._match = path_matcher_fn

    def is_excluded(self, file_path: str) -> bool:
        return any(self._match(file_path, pat) for pat in self._get_patterns())
