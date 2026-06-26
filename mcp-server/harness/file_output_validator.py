""" 
solid-description: Validates file-typed step outputs.
solid-category: service
"""

from __future__ import annotations

from typing import Any

from harness.models import OutputSpec, ValidationResult
from harness.path_checking import PathChecking


class FileOutputValidator:
    """
    solid-description: Validates file-typed step outputs.
    solid-category: service
    """

    def __init__(self, path_checker: PathChecking) -> None:
        self._path_checker = path_checker

    def validate(self, output_spec: OutputSpec, value: Any) -> ValidationResult:
        path_str = str(value)
        if not self._path_checker.exists(path_str):
            return ValidationResult(ok=False, errors=[f"file not found: '{path_str}'"])
        return ValidationResult(ok=True)