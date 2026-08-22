"""
solid-description: Simulates the post-write file content and low-risk classification for Write tool events.
solid-category: service
solid-tags: [hook]
"""

from typing import Protocol

from changed_content import ChangedContent
from simulated_write import SimulatedWrite


"""
solid-name: FileReading
solid-description: Contract for reading text content from a file identity.
solid-category: abstraction
solid-tags: [hook]
"""
class FileReading(Protocol):
    def read_text(self, path: object, encoding: str = "utf-8") -> str: ...


"""
solid-name: EditClassifying
solid-description: Contract for classifying the review risk of a prospective content change.
solid-category: abstraction
solid-tags: [hook]
"""
class EditClassifying(Protocol):
    def is_low_risk(self, old: str, new: str) -> bool: ...


"""
solid-name: DiffChunking
solid-description: Contract for selecting changed content from a prospective file revision.
solid-category: abstraction
solid-tags: [hook]
"""
class DiffChunking(Protocol):
    def chunk(self, old: str, new: str) -> ChangedContent: ...


"""
solid-name: WriteContentSimulator
solid-description: Simulates prospective file content and review risk for a complete write request.
solid-category: service
solid-tags: [hook]
"""
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

    def simulate(self, tool_name: str, tool_input: dict) -> SimulatedWrite:
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        existing, low_risk = "", False
        try:
            existing = self._reader.read_text(file_path)
            changed = self._chunker.chunk(existing, content)
            low_risk = (
                self._classifier.is_low_risk(
                    changed.previous,
                    changed.prospective,
                )
                if changed.previous or changed.prospective
                else True
            )
        except OSError:
            pass
        return SimulatedWrite(
            content=content,
            existing_content=existing,
            low_risk=low_risk,
        )
