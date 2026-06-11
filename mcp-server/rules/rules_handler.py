"""
solid-description: Provides unified access to detection rules and fix instructions.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Any, Optional, Protocol

from rules.detection_rules_loader import DetectionRulesLoading
from rules.fix_instructions_loader import FixInstructionsLoading


class RulesLoading(DetectionRulesLoading, FixInstructionsLoading, Protocol):
    """Composed protocol for both rules loading operations."""


class RulesHandler:
    """Facade composing DetectionRulesLoader and FixInstructionsLoader."""

    def __init__(
        self,
        detection: DetectionRulesLoading,
        fix_instructions: FixInstructionsLoading,
    ) -> None:
        self._detection = detection
        self._fix_instructions = fix_instructions

    def load_detection_rules(
        self, principle: Optional[str] = None, matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        return self._detection.load_detection_rules(principle, matched_tags)

    def load_fix_instructions(self, metric_id: str) -> str:
        return self._fix_instructions.load_fix_instructions(metric_id)
