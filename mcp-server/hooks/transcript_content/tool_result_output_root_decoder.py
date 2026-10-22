"""Decodes output locations from supported transcript content representations."""

from pydantic import TypeAdapter

from harness.flow_validation_error import FlowValidationError
from harness.json_loading import JsonLoader, JsonLoading
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.pydantic_type_adapter_decoder import PydanticTypeAdapterDecoder
from harness.structured_model_decoding import StructuredModelDecoding
from transcript_content.pipeline_output_root import PipelineOutputRoot
from transcript_content.transcript_block_content import TranscriptBlockContent
from transcript_content.transcript_text_content import TranscriptTextContent


"""
solid-name: ToolResultOutputRootDecoder
solid-category: boundary-adapter
solid-description: Reads valid pipeline output locations from textual and block-based transcript tool results.
"""
class ToolResultOutputRootDecoder(StructuredModelDecoding[str]):
    def __init__(
        self,
        content_decoder: StructuredModelDecoding[TranscriptTextContent | TranscriptBlockContent] = PydanticTypeAdapterDecoder(
            TypeAdapter(TranscriptTextContent | TranscriptBlockContent),
        ),
        json_loader: JsonLoading = JsonLoader(),
        output_decoder: StructuredModelDecoding[PipelineOutputRoot] = PydanticModelDecoder(PipelineOutputRoot),
    ) -> None:
        self._content_decoder = content_decoder
        self._json_loader = json_loader
        self._output_decoder = output_decoder

    def decode(self, value: object, description: str) -> str:
        try:
            content = self._content_decoder.decode(value, description)
            raw = self._json_loader.safe_load(content.text)
            return self._output_decoder.decode(raw, description).output_root
        except (FlowValidationError, ValueError, TypeError):
            return ""
