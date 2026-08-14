"""Builds persisted payloads from typed scored review outputs."""

from findings.partial_review_output import PartialReviewOutput
from findings.partial_review_output_payload_building import (
    PartialReviewOutputPayloadBuilding,
)
from findings.reviewed_file_payload_building import ReviewedFilePayloadBuilding


"""
solid-name: PartialReviewOutputPayloadBuilder
solid-category: boundary-adapter
solid-description: Builds one persisted payload from a typed scored review output.
"""
class PartialReviewOutputPayloadBuilder(PartialReviewOutputPayloadBuilding):
    def __init__(self, file_builder: ReviewedFilePayloadBuilding) -> None:
        self._file_builder = file_builder

    def build(self, output: PartialReviewOutput) -> dict:
        return {
            "timestamp": output.timestamp,
            "files": [
                self._file_builder.build(reviewed_file)
                for reviewed_file in output.files
            ],
        }
