"""Provisions the controlled source project used by review comparisons."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory


_TEMPLATE = (
    Path(__file__).resolve().parent
    / "flow_engine"
    / "fixtures"
    / "review_comparison"
    / "source_project"
)


"""
solid-name: ReviewComparisonSourceProject
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Owns one isolated copy of the locked source-only project shared by legacy and workflow review comparisons.
"""
class ReviewComparisonSourceProject:

    def __init__(
        self,
        temporary_directory: TemporaryDirectory[str],
        root: Path,
    ) -> None:
        self._temporary_directory = temporary_directory
        self.root = root
        self.review_target = root / "Sources" / "ReviewTarget.swift"

    @classmethod
    def create(cls) -> ReviewComparisonSourceProject:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="solid-coder-review-comparison-"
        )
        root = Path(temporary_directory.name)
        shutil.copytree(_TEMPLATE, root, dirs_exist_ok=True)
        return cls(temporary_directory, root)

    def cleanup(self) -> None:
        self._temporary_directory.cleanup()
