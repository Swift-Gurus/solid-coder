"""Determines whether a stop event identifies cleanup work."""

from flow_transition_handler import FlowStopApplicabilityChecking
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.structured_model_decoding import StructuredModelDecoding
from pipeline_cleanup.pipeline_cleanup_event import PipelineCleanupEvent


"""
solid-name: PipelineCleanupApplicabilityChecker
solid-category: boundary-adapter
solid-description: Determines whether a host stop event identifies a transcript for pipeline cleanup.
"""
class PipelineCleanupApplicabilityChecker(FlowStopApplicabilityChecking):
    def __init__(self, decoder: StructuredModelDecoding[PipelineCleanupEvent] = PydanticModelDecoder(PipelineCleanupEvent)) -> None:
        self._decoder = decoder

    def applies(self, event: dict) -> bool:
        return bool(self._decoder.decode(event, "cleanup hook event").transcript_path)
