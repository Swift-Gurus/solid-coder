"""Normalizes workflow condition references for expression evaluation."""

from __future__ import annotations

from harness.condition_reference_normalizing import ConditionReferenceNormalizing


"""
solid-name: ConditionReferenceNormalizer
solid-category: service
solid-spec: [SPEC-037]
solid-description: Converts workflow condition references into canonical expression syntax.
"""
class ConditionReferenceNormalizer(ConditionReferenceNormalizing):
    def normalize(self, reference: str) -> str:
        stripped = reference.strip()
        if stripped.startswith("{{") and stripped.endswith("}}"):
            return stripped[2:-2].strip()
        return stripped
