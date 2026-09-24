"""Defines deterministic collection input for one metric step."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence
from harness.step_output_reference import StepOutputReference


"""
solid-name: CollectionMetricCalculation
solid-category: model
solid-spec: [SPEC-053]
solid-description: Carries deterministic collection metric calculation state.
"""
@dataclass(frozen=True)
class CollectionMetricCalculation:
    source: StepOutputReference
    condition: Optional[ConditionDeclaration] = None
    value: int = 0
    source_size: int = 0
    matched_indexes: list[int] = field(default_factory=list)
    excluded_indexes: list[int] = field(default_factory=list)
    condition_evidence: list[ConditionEvidence] = field(default_factory=list)
