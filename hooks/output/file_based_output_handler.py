"""
solid-description: Reads violations from submit_batch_findings output files on disk.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from file_output_reader import OutputReading


class OutputHandling(Protocol):
    def handle(self, raw: Optional[str], path: str, output_dir: Optional[str]) -> Optional[list]: ...


class FileBasedOutputHandler:
    """Output handler that reads violations from submit_batch_findings output files."""

    def __init__(self, output_reader: OutputReading) -> None:
        self._output_reader = output_reader

    def handle(self, raw: Optional[str], path: str, output_dir: Optional[str]) -> list:
        if output_dir is None:
            raise ValueError("FileBasedOutputHandler requires output_dir")
        return self._output_reader.read_violations(output_dir, path)
