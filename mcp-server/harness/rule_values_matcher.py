"""Matches values within one rule-selection dimension."""

from harness.collection_value_matching import CollectionValueMatching
from harness.rule_value_match_mode import RuleValueMatchMode


"""
solid-name: RuleValuesMatcher
solid-category: service
solid-spec: [SPEC-039]
solid-description: Selects values that are present in or missing from one rule-selection candidate collection.
"""
class RuleValuesMatcher:
    def __init__(self, collection_matcher: CollectionValueMatching) -> None:
        self._collection_matcher = collection_matcher

    def match(
        self,
        candidates: list[object],
        selected: list[object],
        mode: RuleValueMatchMode,
    ) -> list[object]:
        if mode is RuleValueMatchMode.PRESENT:
            return [
                candidate
                for candidate in candidates
                if self._collection_matcher.contains(selected, candidate)
            ]
        return [
            candidate
            for candidate in candidates
            if not self._collection_matcher.contains(selected, candidate)
        ]
