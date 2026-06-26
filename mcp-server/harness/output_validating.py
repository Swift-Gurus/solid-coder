"""
solid-description: Contract for validating output values against specifications.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Any, Protocol

from harness.models import OutputSpec, ValidationResult


class OutputValidating(Protocol):
    """
    solid-description: Contract for validating output values against specifications.
    solid-category: abstraction
    """

    def validate(self, output_spec: OutputSpec, value: Any) -> ValidationResult: ...