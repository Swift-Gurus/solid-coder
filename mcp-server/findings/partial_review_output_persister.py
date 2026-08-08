"""Coordinates persistence of rendered immutable review outputs."""

from pathlib import Path

from findings.partial_review_output import PartialReviewOutput
from findings.partial_review_output_persisting import PartialReviewOutputPersisting
from findings.partial_review_output_rendering import PartialReviewOutputRendering
from findings.text_file_writing import TextFileWriting


"""
solid-name: PartialReviewOutputPersister
solid-category: service
solid-description: Persists a rendered immutable review output at its requested destination.
"""
class PartialReviewOutputPersister(PartialReviewOutputPersisting):
    def __init__(
        self,
        renderer: PartialReviewOutputRendering,
        writer: TextFileWriting,
    ) -> None:
        self._renderer = renderer
        self._writer = writer

    def persist(self, output: PartialReviewOutput, output_path: Path) -> None:
        self._writer.write(output_path, self._renderer.render(output))
