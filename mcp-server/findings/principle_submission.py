"""Defines one immutable principle-labelled review submission."""

from __future__ import annotations

from dataclasses import dataclass

from findings.partial_review_output import PartialReviewOutput


"""
solid-name: PrincipleSubmission
solid-category: model
solid-description: Associates a principle label with its immutable partial review output.
"""
@dataclass(frozen=True)
class PrincipleSubmission:
    label: str
    output: PartialReviewOutput
