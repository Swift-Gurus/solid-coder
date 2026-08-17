"""Defines parsing of workflow comparison operations."""

from collections.abc import Mapping
from typing import Protocol

from harness.comparison_operation import ComparisonOperation


"""
solid-name: ComparisonOperationParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for parsing one validated workflow comparison operation.
"""
class ComparisonOperationParsing(Protocol):
    def parse(self, raw: Mapping[object, object]) -> ComparisonOperation: ...
