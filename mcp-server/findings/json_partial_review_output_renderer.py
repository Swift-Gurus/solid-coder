"""Renders immutable scored review outputs as JSON text."""

from findings.partial_review_output import PartialReviewOutput
from findings.partial_review_output_payload_building import (
    PartialReviewOutputPayloadBuilding,
)
from findings.partial_review_output_rendering import PartialReviewOutputRendering
from json_serializer import JsonSerializing


"""
solid-name: JsonPartialReviewOutputRenderer
solid-category: boundary-adapter
solid-description: Produces persisted review-output text from typed scored review data.
"""
class JsonPartialReviewOutputRenderer(PartialReviewOutputRendering):
    def __init__(
        self,
        serializer: JsonSerializing,
        payload_builder: PartialReviewOutputPayloadBuilding,
    ) -> None:
        self._serializer = serializer
        self._payload_builder = payload_builder

    def render(self, output: PartialReviewOutput) -> str:
        return self._serializer.serialize(
            self._payload_builder.build(output),
            indent=2,
        )
