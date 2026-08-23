"""Defines closed reuse classifications for DRY repository candidates."""

from enum import Enum


"""
solid-name: DRYReuseClassification
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Represents whether an existing candidate can satisfy or extend the reviewed responsibility.
"""
class DRYReuseClassification(str, Enum):
    EXACT = "EXACT"
    EXTENSIBLE = "EXTENSIBLE"
    PARTIAL = "PARTIAL"
    NOT_SUITABLE = "NOT_SUITABLE"
