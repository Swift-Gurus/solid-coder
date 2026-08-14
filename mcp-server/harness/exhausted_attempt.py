"""Defines one exhausted workflow-step attempt budget."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: ExhaustedAttempt
solid-category: model
solid-spec: [SPEC-010, SPEC-031]
solid-description: Identifies an exhausted execution attempt and its declared workflow step.
"""
@dataclass(frozen=True)
class ExhaustedAttempt:
    attempt_id: str
    step_id: str
