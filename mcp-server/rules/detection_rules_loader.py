"""
solid-description: Provides detection rules for a specified principle or for all principles matching given tags.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from rules import discover_principles as _dp
from rules.principle_content_building import PrincipleContentBuilding


class AllPrinciplesProviding(Protocol):
    def all_principles(self) -> list: ...


class DetectionRulesLoading(Protocol):
    def load_detection_rules(
        self, principle: Optional[str], matched_tags: Optional[list],
    ) -> dict: ...


class DetectionRulesLoader:
    """Discovers active principles and delegates content assembly to PrincipleContentBuilding."""

    def __init__(
        self,
        all_principles: AllPrinciplesProviding,
        refs_root: Path,
        content_builder: PrincipleContentBuilding,
        discover_fn: Optional[Callable] = None,
    ) -> None:
        self._all_principles = all_principles
        self._refs_root = refs_root
        self._content_builder = content_builder
        self._discover_fn = discover_fn or _dp.discover_and_filter

    def load_detection_rules(
        self,
        principle: Optional[str] = None,
        matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        all_p = self._all_principles.all_principles()

        if principle:
            m = next((p for p in all_p if p["name"].lower() == principle.lower()), None)
            if not m:
                available = ", ".join(p["name"] for p in all_p)
                return {"error": f"Principle '{principle}' not found. Available: {available}"}
            return {"principles": [self._content_builder.build(m)]}

        if matched_tags is None:
            active = all_p
        else:
            tags: list = matched_tags if isinstance(matched_tags, list) else ([] if matched_tags in ("", []) else [matched_tags])
            active = self._discover_fn(str(self._refs_root), matched_tags=tags)["active_principles"]
        return {"principles": [self._content_builder.build(p) for p in active]}
