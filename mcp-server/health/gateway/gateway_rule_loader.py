"""Coordinates legacy rule discovery and detection-rule loading."""

from typing import Protocol

from health.gateway.gateway_candidate_tags_loader import CandidateTagsLoading
from health.gateway.gateway_detection_rules_loader import MatchedDetectionRulesLoading

"""
solid-name: RulesLoading
solid-category: abstraction
solid-description: Contract for accessing legacy review discovery tags and matched detection rules.
"""


class RulesLoading(CandidateTagsLoading, MatchedDetectionRulesLoading, Protocol):
    pass


"""
solid-name: GatewayRuleLoader
solid-category: facade
solid-description: Delegates legacy rule discovery and detection loading to their dedicated capabilities.
"""


class GatewayRuleLoader:
    def __init__(
        self,
        tags: CandidateTagsLoading,
        detection: MatchedDetectionRulesLoading,
    ) -> None:
        self._tags = tags
        self._detection = detection

    def get_candidate_tags(self) -> list:
        return self._tags.get_candidate_tags()

    def load_detection_rules(self, matched_tags: list) -> dict | None:
        return self._detection.load_detection_rules(matched_tags)
