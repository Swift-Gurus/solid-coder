"""
solid-description: Appends entries to files.
solid-category: utility
solid-tags: [hook, llm]
"""

import json
from pathlib import Path
from typing import Protocol


class LogEntryWriting(Protocol):
    def append(self, dir_path: Path, filename: str, entry: dict) -> None: ...


class JsonlEntryWriter:
    """Boundary adapter: appends JSON lines to disk files."""

    def append(self, dir_path: Path, filename: str, entry: dict) -> None:
        try:
            with (dir_path / filename).open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
