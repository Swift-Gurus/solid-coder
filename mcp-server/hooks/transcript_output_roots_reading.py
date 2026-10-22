"""Defines transcript-owned output discovery."""

from typing import Protocol


"""
solid-name: TranscriptOutputRootsReading
solid-category: abstraction
solid-description: Contract for reading the distinct pipeline output locations recorded in a session transcript.
"""
class TranscriptOutputRootsReading(Protocol):
    def __call__(self, transcript_path: str) -> list[str]: ...
