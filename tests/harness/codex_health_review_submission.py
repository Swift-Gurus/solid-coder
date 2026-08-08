"""Defines one health-review submission observed in a Codex transcript."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: CodexHealthReviewSubmission
solid-category: value
solid-description: Identifies the reviewed file and submitted principles for one isolated Codex health-review session.
"""
@dataclass(frozen=True)
class CodexHealthReviewSubmission:

    file_name: str
    principle_names: frozenset[str]
    transcript_path: Path
    successful: bool
