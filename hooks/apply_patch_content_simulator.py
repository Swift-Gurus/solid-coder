"""
solid-description: Simulates the post-apply file content for apply_patch tool events.
solid-category: service
solid-tags: [hook]
"""

from pathlib import Path
from typing import Protocol


class PatchParsing(Protocol):
    def parse(self, command: str) -> list: ...
    def add_content(self, lines: list) -> str: ...
    def apply_update(self, existing_content: str, body_lines: list) -> str: ...


class FileReading(Protocol):
    def read_text(self, path: object, encoding: str = "utf-8") -> str: ...


class ApplyPatchContentSimulator:
    """Simulates the resulting file content for the first affected source file in an apply_patch command."""

    def __init__(self, parser: PatchParsing, file_reader: FileReading) -> None:
        self._parser = parser
        self._reader = file_reader

    def simulate(self, tool_input: dict) -> tuple:
        command = tool_input.get("command", "")
        entries = [e for e in self._parser.parse(command) if e["operation"] != "delete"]
        if not entries:
            return "", "", True
        entry = entries[0]
        file_path = entry["path"]
        if entry["operation"] == "add":
            return self._parser.add_content(entry["lines"]), "", False
        try:
            existing = self._reader.read_text(file_path)
            content = self._parser.apply_update(existing, entry["lines"])
            return content, existing, False
        except OSError:
            return "", "", True

    def first_file_path(self, command: str) -> str:
        entries = [e for e in self._parser.parse(command) if e["operation"] != "delete"]
        return entries[0]["path"] if entries else ""
