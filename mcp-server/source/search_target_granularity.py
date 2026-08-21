"""Defines deterministic source-search target granularities."""

from enum import Enum


"""
solid-name: SearchTargetGranularity
solid-category: model
solid-spec: [SPEC-040]
solid-description: Selects complete-file or parsed-unit preparation for source-search targets.
"""
class SearchTargetGranularity(str, Enum):
    FILE = "file"
    UNIT = "unit"
