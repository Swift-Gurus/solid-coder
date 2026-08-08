"""Defines computation of operation output paths."""

from typing import Protocol


"""
solid-name: OutputPathComputing
solid-category: abstraction
solid-description: Contract for computing standardized output locations for model-facing operations.
"""
class OutputPathComputing(Protocol):
    def compute(self, operation: str, spec_number: str = "") -> dict: ...
