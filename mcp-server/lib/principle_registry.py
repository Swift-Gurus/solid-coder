#!/usr/bin/env python3
"""
solid-description: Service that provides a unified list of all available principles — both active and skipped — discovered from a given references directory.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Callable, Optional

from lib import discover_principles


class PrincipleRegistry:
    """Discovers and provides all principles from a references directory."""

    def __init__(
        self,
        refs_root: Path,
        discover_fn: Optional[Callable] = None,
    ) -> None:
        self._refs_root = refs_root
        self._discover_fn = discover_fn or discover_principles.discover_and_filter

    def all_principles(self) -> list:
        """Return combined list of active and skipped principles."""
        result = self._discover_fn(str(self._refs_root))
        return result.get("active_principles", []) + result.get("skipped_principles", [])
