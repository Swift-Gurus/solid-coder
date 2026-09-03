"""Defines sibling identity for one combined rule-presentation group."""

from dataclasses import dataclass


"""
solid-name: CombinedRuleBatchStepGroupIdentity
solid-category: model
solid-spec: [SPEC-043]
solid-description: Groups compatible ready rule steps by their enclosing authored presentation group without encoding identity into step strings.
"""
@dataclass(frozen=True)
class CombinedRuleBatchStepGroupIdentity:
    group_alias: str
