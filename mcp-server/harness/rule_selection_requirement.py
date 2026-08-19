"""Defines included-value requirements for one rule selection."""

from enum import Enum


"""
solid-name: RuleSelectionRequirement
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents whether any or every included value must match a review unit.
"""
class RuleSelectionRequirement(str, Enum):
    ANY = "any"
    ALL = "all"
