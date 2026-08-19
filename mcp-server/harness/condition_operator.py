"""Defines supported workflow condition comparison operators."""

from __future__ import annotations

from enum import Enum


"""
solid-name: ConditionOperator
solid-category: model
solid-spec: [SPEC-037]
solid-description: Enumerates the supported comparison operations for workflow conditions.
"""
class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EXISTS = "exists"
