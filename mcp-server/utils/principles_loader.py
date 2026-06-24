"""
solid-description: Loads principles applicable to the provided content.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from hc_rule_loader import RulesLoading
from hc_tag_detector import TagDetecting
from utils.debug_logger import Observing


class PrinciplesLoading(Protocol):
    def load(self, content: str, path: str) -> Optional[list]: ...


class PrinciplesLoader:
    """Detects active tags from content and fetches matching detection rules."""

    def __init__(self, rules: RulesLoading, tags: TagDetecting) -> None:
        self._rules = rules
        self._tags = tags

    @Observing("gate.principles_loader.load")
    def load(self, content: str, path: str) -> Optional[list]:
        candidate_tags = self._rules.get_candidate_tags()
        matched_tags = self._tags.detect(content, candidate_tags)
        detection_data = self._rules.load_detection_rules(matched_tags)
        if not detection_data:
            return None
        return detection_data.get("principles", [])
