"""
solid-description: Provides scored findings submission capabilities.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Protocol

from findings.json_file_writer import JsonFileWriting

"""
solid-name: FindingsSubmitting
solid-category: abstraction
solid-description: Contract for persisting scored findings.
"""


class FindingsSubmitting(Protocol):
    def submit(
        self,
        timestamp: str,
        scored_files: list,
        output_path: str,
    ) -> dict | None: ...


"""
solid-name: FindingsSubmitter
solid-category: service
solid-description: Submits scored findings for persistence.
"""


class FindingsSubmitter:
    """Writes a scored output document to disk."""

    def __init__(self, file_writer: JsonFileWriting) -> None:
        self._file_writer = file_writer

    def submit(
        self,
        timestamp: str,
        scored_files: list,
        output_path: str,
    ) -> dict | None:
        doc = {"timestamp": timestamp, "files": scored_files}
        self._file_writer.write(output_path, doc)
        return None
