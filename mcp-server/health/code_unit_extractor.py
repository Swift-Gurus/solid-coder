"""
solid-name: CodeUnitExtractor
solid-category: service
solid-description: Extracts top-level code unit names from source code.
"""

import re
from typing import Protocol


class CodeUnitExtracting(Protocol):
    def extract(self, content: str, language: str) -> list: ...


class CodeUnitExtractor(CodeUnitExtracting):
    """Extracts top-level declaration names from source content.

    Uses conservative patterns that match the preamble's definition of a code unit:
    top-level class, struct, enum, protocol, actor, extension (Swift) or
    top-level class / function (Python). Intentionally over-counts rather than
    under-counts — the goal is to detect when a model submitted zero units for a
    non-empty file, not to precisely enumerate every declaration.
    """

    _SWIFT = re.compile(
        r"^\s*(?:(?:public|internal|private|open|final|@\w+)\s+)*"
        r"(?:class|struct|enum|protocol|actor|extension)\s+(\w+)",
        re.MULTILINE,
    )
    _PYTHON = re.compile(r"^(?:class|def)\s+(\w+)", re.MULTILINE)

    def extract(self, content: str, language: str) -> list:
        pattern = self._PYTHON if language.lower() == "python" else self._SWIFT
        return list(dict.fromkeys(m.group(1) for m in pattern.finditer(content)))