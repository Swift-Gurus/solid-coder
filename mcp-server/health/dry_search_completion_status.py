"""Defines health-check DRY-search completion states."""

from enum import Enum


"""
solid-name: DrySearchCompletionStatus
solid-category: model
solid-description: Enumerates whether DRY-search proof is unnecessary, present, or missing for a health-check run.
"""
class DrySearchCompletionStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    COMPLETE = "complete"
    MISSING = "missing"
