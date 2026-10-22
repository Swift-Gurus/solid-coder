"""Adapts host cleanup events to transcript-scoped cleanup execution."""

from typing import Protocol

from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.structured_model_decoding import StructuredModelDecoding
from pipeline_cleanup.pipeline_cleanup_event import PipelineCleanupEvent
from pipeline_cleanup.pipeline_output_cleanup import PipelineOutputCleaning


"""
solid-name: PipelineCleanupHandling
solid-category: abstraction
solid-description: Contract for handling host stop events that request pipeline-output cleanup.
"""
class PipelineCleanupHandling(Protocol):
    def handle(self, event: dict) -> None: ...


"""
solid-name: PipelineCleanupHandler
solid-category: boundary-adapter
solid-description: Translates host cleanup requests into transcript-scoped pipeline-output cleanup.
"""
class PipelineCleanupHandler(PipelineCleanupHandling):
    def __init__(
        self,
        cleanup: PipelineOutputCleaning,
        decoder: StructuredModelDecoding[PipelineCleanupEvent] = PydanticModelDecoder(PipelineCleanupEvent),
    ) -> None:
        self._cleanup = cleanup
        self._decoder = decoder

    def handle(self, event: dict) -> None:
        request = self._decoder.decode(event, "cleanup hook event")
        self._cleanup.clean(request.transcript_path or "")
