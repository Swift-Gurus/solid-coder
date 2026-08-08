"""Defines a labelled batch-submission parsing failure."""

from dataclasses import dataclass


"""
solid-name: BatchSubmissionParseFailure
solid-category: model
solid-description: Identifies the first principle payload rejected while parsing an ordered batch submission.
"""
@dataclass(frozen=True)
class BatchSubmissionParseFailure:
    principle_label: str
    message: str
