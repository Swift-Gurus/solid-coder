"""Defines the result of validating a workflow value."""

from __future__ import annotations

from dataclasses import dataclass, field


"""
solid-name: ValidationResult
solid-category: model
solid-spec: [SPEC-030]
solid-description: Represents whether validation succeeded and every validation error returned to the caller.
"""
@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
