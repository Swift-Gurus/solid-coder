"""Exports the sealed workflow condition-evidence family."""

from typing import Union

from harness.comparison_condition_evidence import ComparisonConditionEvidence
from harness.composite_condition_evidence import CompositeConditionEvidence
from harness.unavailable_condition_evidence import UnavailableConditionEvidence


ConditionEvidence = Union[
    ComparisonConditionEvidence,
    CompositeConditionEvidence,
    UnavailableConditionEvidence,
]


__all__ = [
    "ComparisonConditionEvidence",
    "CompositeConditionEvidence",
    "ConditionEvidence",
    "UnavailableConditionEvidence",
]
