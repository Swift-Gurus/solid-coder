"""Defines parsing of NUL-delimited path output."""

from typing import Protocol


"""
solid-name: NulDelimitedPathsParsing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for parsing stable project-relative paths from NUL-delimited command output.
"""
class NulDelimitedPathsParsing(Protocol):
    def parse(self, output: str) -> list[str]: ...
