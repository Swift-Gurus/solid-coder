"""Builds persisted payloads for typed reviewed files."""

from findings.review_unit_payload_building import ReviewUnitPayloadBuilding
from findings.reviewed_file import ReviewedFile
from findings.reviewed_file_payload_building import ReviewedFilePayloadBuilding


"""
solid-name: ReviewedFilePayloadBuilder
solid-category: boundary-adapter
solid-description: Builds the persisted path and reviewed units for one file.
"""
class ReviewedFilePayloadBuilder(ReviewedFilePayloadBuilding):
    def __init__(self, unit_builder: ReviewUnitPayloadBuilding) -> None:
        self._unit_builder = unit_builder

    def build(self, reviewed_file: ReviewedFile) -> dict:
        return {
            "file_path": reviewed_file.file_path,
            "units": [
                self._unit_builder.build(unit)
                for unit in reviewed_file.units
            ],
        }
