"""
solid-description: Loads principles applicable to the provided content.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from hc_rule_loader import RulesLoading
from hc_tag_detector import TagDetecting
from utils.debug_logger import Observing


"""
solid-name: PrinciplesLoading
solid-category: abstraction
solid-description: Contract for loading the health-check principles applicable to one source request.
solid-tags: [hook, llm]
"""
class PrinciplesLoading(Protocol):
    def load(
        self,
        content: str,
        path: str,
        principle_names: Optional[list[str]] = None,
    ) -> Optional[list]: ...


"""
solid-name: PrinciplesLoader
solid-category: service
solid-description: Loads applicable health-check principles and applies an explicit request scope when declared.
solid-tags: [hook, llm]
"""
class PrinciplesLoader:
    """Detects active tags from content and fetches matching detection rules."""

    def __init__(self, rules: RulesLoading, tags: TagDetecting) -> None:
        self._rules = rules
        self._tags = tags

    @Observing("gate.principles_loader.load")
    def load(
        self,
        content: str,
        path: str,
        principle_names: Optional[list[str]] = None,
    ) -> Optional[list]:
        candidate_tags = self._rules.get_candidate_tags()
        matched_tags = self._tags.detect(content, candidate_tags)
        detection_data = self._rules.load_detection_rules(matched_tags)
        if not detection_data:
            return None
        principles = detection_data.get("principles", [])
        if not principle_names:
            return principles

        selected = []
        missing = []
        for requested_name in principle_names:
            principle = next(
                (
                    candidate
                    for candidate in principles
                    if candidate.get("name", "").casefold()
                    == requested_name.casefold()
                ),
                None,
            )
            if principle is None:
                missing.append(requested_name)
            else:
                selected.append(principle)
        if missing:
            raise ValueError(
                "Requested health-check principles were not loaded: "
                + ", ".join(missing)
            )
        return selected
