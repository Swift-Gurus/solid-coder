"""
solid-description: Writes structured data as JSON to output files.
solid-category: service
solid-tags: [utility, service]
"""

import sys
from pathlib import Path
from typing import Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from json_serializer import JsonSerializing  # noqa: E402


class JsonFileWriting(Protocol):
    def write(self, output_path: str, doc: dict) -> None: ...


class JsonFileWriter:
    """Boundary adapter: writes a dict to a JSON file on disk."""

    def __init__(self, serializer: JsonSerializing) -> None:
        self._serializer = serializer

    def write(self, output_path: str, doc: dict) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(self._serializer.serialize(doc, indent=2), encoding="utf-8")
