"""
solid-description: Simulates the post-edit file content and low-risk classification for Edit tool events.
solid-category: service
solid-tags: [hook]
"""

from typing import Protocol


class FileReading(Protocol):
    def read_text(self, path: object, encoding: str = "utf-8") -> str: ...


class EditClassifying(Protocol):
    def is_low_risk(self, old: str, new: str) -> bool: ...


class EditContentSimulator:
    """Simulates the resulting file content and low-risk status for an Edit tool event."""

    def __init__(self, file_reader: FileReading, classifier: EditClassifying) -> None:
        self._reader = file_reader
        self._classifier = classifier

    def simulate(self, tool_input: dict) -> tuple:
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        low_risk = self._classifier.is_low_risk(old_string, new_string)
        existing = ""
        try:
            existing = self._reader.read_text(file_path)
            content = existing.replace(old_string, new_string) if replace_all \
                      else existing.replace(old_string, new_string, 1)
        except OSError:
            content = new_string
        return content, existing, low_risk
