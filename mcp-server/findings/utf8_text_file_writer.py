"""Writes rendered output text using UTF-8 encoding."""

from pathlib import Path

from findings.text_file_writing import TextFileWriting


"""
solid-name: Utf8TextFileWriter
solid-category: boundary-adapter
solid-description: Persists rendered text content as a UTF-8 encoded file.
"""
class Utf8TextFileWriter(TextFileWriting):
    def write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
