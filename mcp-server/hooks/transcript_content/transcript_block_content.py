"""Exposes the first textual block of host tool-result content."""

from pydantic import RootModel

from transcript_content.transcript_content_block import TranscriptContentBlock


"""
solid-name: TranscriptBlockContent
solid-category: model
solid-description: Provides the first textual content from an ordered collection of transcript blocks.
"""
class TranscriptBlockContent(RootModel[list[TranscriptContentBlock]]):
    @property
    def text(self) -> str:
        for block in self.root:
            if block.type == "text":
                return block.text or ""
        return ""
