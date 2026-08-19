"""Defines matching operations for rule-selection values."""

from typing import Protocol

from harness.rule_value_match_mode import RuleValueMatchMode


"""
solid-name: RuleValuesMatching
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for selecting values by their presence within a rule-selection dimension.
"""
class RuleValuesMatching(Protocol):

    def match(
        self,
        candidates: list[object],
        selected: list[object],
        mode: RuleValueMatchMode,
    ) -> list[object]: ...
