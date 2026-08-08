"""Defines one immutable findings batch submission."""

from __future__ import annotations

from dataclasses import dataclass

from findings.principle_submission import PrincipleSubmission


"""
solid-name: BatchSubmission
solid-category: model
solid-description: Represents the immutable principle submissions contained in one review request.
"""
@dataclass(frozen=True)
class BatchSubmission:
    principles: tuple[PrincipleSubmission, ...]
