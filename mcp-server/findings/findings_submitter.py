"""
solid-description: Submits scored findings output for persistence.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Optional, Protocol

from findings.json_file_writer import JsonFileWriting, JsonFileWriter


class FindingsSubmitting(Protocol):
    def submit(
        self,
        timestamp: str,
        scored_files: list,
        output_path: str,
    ) -> Optional[dict]: ...


class FindingsSubmitter:
    """Writes a scored output document to disk."""

    def __init__(self, file_writer: JsonFileWriting) -> None:
        self._file_writer = file_writer

    def submit(
        self,
        timestamp: str,
        scored_files: list,
        output_path: str,
    ) -> Optional[dict]:
        doc = {"timestamp": timestamp, "files": scored_files}
        self._file_writer.write(output_path, doc)
        return None
