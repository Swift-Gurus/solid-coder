"""
solid-description: Provides access to all available principles.
solid-category: service
solid-tags: [utility, service]
"""

from collections.abc import Callable
from pathlib import Path

from rules import discover_principles


class PrincipleRegistry:
    """Discovers and provides all principles from a references directory."""

    def __init__(
        self,
        refs_root: Path,
        discover_fn: Callable | None = None,
    ) -> None:
        self._refs_root = refs_root
        self._discover_fn = discover_fn or discover_principles.discover_and_filter

    def all_principles(self) -> list:
        """Return combined list of active and skipped principles."""
        result = self._discover_fn(str(self._refs_root))
        return result.get("active_principles", []) + result.get(
            "skipped_principles", []
        )
