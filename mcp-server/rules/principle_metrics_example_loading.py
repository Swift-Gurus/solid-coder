"""Defines loading of principle metric examples from review schemas."""

from pathlib import Path
from typing import Protocol


"""
solid-name: PrincipleMetricsExampleLoading
solid-category: abstraction
solid-description: Contract for loading all LLM-facing metric examples declared by one principle review schema.
"""
class PrincipleMetricsExampleLoading(Protocol):
    def load(self, schema_path: Path) -> dict: ...
