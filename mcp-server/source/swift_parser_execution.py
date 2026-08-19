"""Defines one structured Swift parser subprocess request."""

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: SwiftParserExecution
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents an ordered Swift parser invocation for one temporary source file.
"""
@dataclass(frozen=True)
class SwiftParserExecution:
    source_path: Path

    def process_arguments(self) -> list[str]:
        return [
            "swiftc",
            "-frontend",
            "-dump-parse",
            "-dump-ast-format",
            "json",
            str(self.source_path),
        ]
