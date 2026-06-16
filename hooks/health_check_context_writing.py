"""
solid-description: Utility for writing output to a file based on language.
solid-category: utility
solid-tags: [hook, utility]
"""

from typing import Protocol


class HealthCheckContextWriting(Protocol):
    def write(self, output_dir: str, file_path: str, language: str) -> None: ...
