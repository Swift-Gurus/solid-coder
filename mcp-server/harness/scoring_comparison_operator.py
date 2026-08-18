"""Defines supported deterministic scoring comparison operators."""

from enum import Enum


"""
solid-name: ScoringComparisonOperator
solid-category: model
solid-spec: [SPEC-012, SPEC-039]
solid-description: Enumerates the closed comparison operations accepted by engine-owned score bands.
"""
class ScoringComparisonOperator(str, Enum):
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
