"""Defines loading of pipeline synthesis context."""

from typing import Protocol


"""
solid-name: ContextLoading
solid-category: abstraction
solid-description: Contract for loading synthesis context from review outputs.
"""
class ContextLoading(Protocol):
    def load_context(self, output_root: str) -> dict: ...
