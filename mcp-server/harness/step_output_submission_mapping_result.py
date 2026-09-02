"""Carries boundary output-key translation or its deterministic rejection."""

from dataclasses import dataclass
from typing import Optional


"""
solid-name: StepOutputSubmissionMappingResult
solid-category: model
solid-spec: [SPEC-042]
solid-description: Represents translated step-output submissions or the reason their domain labels were rejected.
"""
@dataclass(frozen=True)
class StepOutputSubmissionMappingResult:
    outputs: dict
    error: Optional[str] = None
