"""Defines closed implementation-duplication classifications for DRY candidates."""

from enum import Enum


"""
solid-name: DRYDuplicationClassification
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Represents whether candidate code duplicates an implemented logical sequence from the reviewed unit.
"""
class DRYDuplicationClassification(str, Enum):
    IDENTICAL = "IDENTICAL"
    STRUCTURAL = "STRUCTURAL"
    SIMILAR = "SIMILAR"
    NOT_DUPLICATE = "NOT_DUPLICATE"
