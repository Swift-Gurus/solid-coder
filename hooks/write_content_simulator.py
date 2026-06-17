"""
solid-description: Simulates the post-write file content and low-risk classification for Write tool events.
solid-category: service
solid-tags: [hook]
"""

from typing import Protocol


class FileReading(Protocol):
    def read_text(self, path: object, encoding: str = "utf-8") -> str: ...


class EditClassifying(Protocol):
    def is_low_risk(self, old: str, new: str) -> bool: ...


class DiffChunking(Protocol):
    def chunk(self, old: str, new: str) -> tuple: ...


class WriteContentSimulator:
    """Simulates the resulting file content and low-risk status for a Write tool event."""

    def __init__(
        self,
        file_reader: FileReading,
        classifier: EditClassifying,
        chunker: DiffChunking,
    ) -> None:
        self._reader = file_reader
        self._classifier = classifier
        self._chunker = chunker

    def simulate(self, tool_input: dict) -> tuple:
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        existing, low_risk = "", False
        try:
            existing = self._reader.read_text(file_path)
            old_chunk, new_chunk = self._chunker.chunk(existing, content)
            low_risk = self._classifier.is_low_risk(old_chunk, new_chunk) if (old_chunk or new_chunk) else True
        except OSError:
            pass
        return content, existing, low_risk
