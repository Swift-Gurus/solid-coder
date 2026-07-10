"""
solid-description: Identifies write operations that target protected files.
solid-category: service
solid-tags: [hook]
"""

import re
from typing import Optional, Tuple


class BashWriteGate:
    """Detects Bash commands that write to protected source-code file extensions."""

    _PROTECTED = (".swift", ".kt", ".java")

    _WRITE_PATTERNS: list[Tuple[str, int, str]] = [
        (r'\btee\b', 0, "tee"),
        (r"<<\s*['\"]?[A-Z_a-z]+['\"]?\s*>", 0, "heredoc redirect"),
        (r"(?<![0-9&2])>{1,2}(?!&\d|/dev/null|\s*$)\s*\S", 0, "output redirect (> or >>)"),
        (r"\bsed\b.*\s-[a-zA-Z]*i", 0, "sed in-place (-i)"),
        (r"\bperl\b.*\s-[a-zA-Z]*i", 0, "perl in-place (-i)"),
        (r"\bpython3?\b.*\bopen\s*\(.*['\"][wa][bt+]{0,3}['\"]", re.DOTALL, "python open write"),
    ]

    _SAFE_PATTERNS = [
        r">{1,2}\s*/dev/null",
        r">&\s*[0-9]",
        r"2>{1,2}",
    ]

    def _targets_protected_file(self, command: str) -> bool:
        return any(ext in command for ext in self._PROTECTED)

    def check(self, command: str) -> Optional[str]:
        """Return the matched write-pattern name if command writes to a protected file, else None."""
        if not self._targets_protected_file(command):
            return None
        sanitized = command
        for safe in self._SAFE_PATTERNS:
            if re.search(safe, sanitized):
                sanitized = re.sub(safe, "", sanitized)
        for pattern, flags, name in self._WRITE_PATTERNS:
            if re.search(pattern, sanitized, flags):
                return name
        return None
