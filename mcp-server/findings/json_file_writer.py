"""
solid-description: Persists structured data to output files.
solid-category: service
solid-tags: [utility, service]
"""

import json
from pathlib import Path
from typing import Protocol


class JsonFileWriting(Protocol):
    def write(self, output_path: str, doc: dict) -> None: ...


class JsonFileWriter:
    """Boundary adapter: writes a dict to a JSON file on disk."""

    def write(self, output_path: str, doc: dict) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(doc, indent=2), encoding="utf-8")