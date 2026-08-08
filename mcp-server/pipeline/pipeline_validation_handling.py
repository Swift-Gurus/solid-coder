"""Defines pipeline architecture and findings validation."""

from typing import Protocol


"""
solid-name: PipelineValidationHandling
solid-category: abstraction
solid-description: Contract for validating architecture plans and scored review findings.
"""
class PipelineValidationHandling(Protocol):
    def validate_architecture(self, arch_path: str) -> dict: ...

    def validate_findings(self, output_root: str) -> dict: ...
