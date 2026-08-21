"""Defines the execution granularity of a review rule workflow."""

from enum import Enum


"""
solid-name: RuleScope
solid-category: model
solid-spec: [SPEC-039]
solid-description: Identifies whether one review rule executes for each normalized unit or once for its containing file.
"""
class RuleScope(str, Enum):
    UNIT = "unit"
    FILE = "file"
