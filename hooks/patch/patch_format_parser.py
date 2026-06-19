"""
solid-description: Extracts file operations from command text.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Optional


class PatchFormatParser:
    """Parses apply_patch command strings into structured file operation entries."""

    _HEADERS = {
        "*** Add File: ": "add",
        "*** Update File: ": "update",
        "*** Delete File: ": "delete",
    }

    def parse(self, command: str) -> list:
        """Return a list of {path, operation, lines} dicts, one per file section."""
        entries: list = []
        current: Optional[dict] = None
        for line in command.splitlines():
            header = self._parse_header(line)
            if header:
                if current:
                    entries.append(current)
                path, operation = header
                current = {"path": path, "operation": operation, "lines": []}
            elif line.startswith("*** Move to: ") or line in ("*** Begin Patch", "*** End Patch"):
                pass
            elif current is not None:
                current["lines"].append(line)
        if current:
            entries.append(current)
        return entries

    def _parse_header(self, line: str) -> Optional[tuple]:
        for prefix, operation in self._HEADERS.items():
            if line.startswith(prefix):
                return line[len(prefix):].strip(), operation
        return None