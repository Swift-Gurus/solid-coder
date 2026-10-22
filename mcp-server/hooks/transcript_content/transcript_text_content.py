"""Exposes plain textual tool-result content."""

from pydantic import RootModel


"""
solid-name: TranscriptTextContent
solid-category: model
solid-description: Represents plain textual content in a host transcript.
"""
class TranscriptTextContent(RootModel[str]):
    @property
    def text(self) -> str:
        return self.root
