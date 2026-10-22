"""Defines cleanup path eligibility."""

from typing import Protocol


"""
solid-name: OutputPathSafetyChecking
solid-category: abstraction
solid-description: Contract for determining whether an output location is eligible for safe cleanup.
"""
class OutputPathSafetyChecking(Protocol):
    def __call__(self, path: str) -> bool: ...
