"""Defines how rule-selection values are matched."""

from enum import Enum


"""
solid-name: RuleValueMatchMode
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents whether rule-selection evaluation needs present or missing values.
"""
class RuleValueMatchMode(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
