"""
solid-description: Service providing unified patch processing through protocol-typed dependency injection.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Protocol


class PatchFormatParsing(Protocol):
    def parse(self, command: str) -> list: ...


class ContentExtracting(Protocol):
    def add_content(self, lines: list) -> str: ...


class HunkApplying(Protocol):
    def apply_update(self, existing_content: str, body_lines: list) -> str: ...


class ApplyPatchParser:
    """Facade: composes three subsystems for protocol-typed injection at call sites."""

    def __init__(
        self,
        format_parser: PatchFormatParsing,
        content_extractor: ContentExtracting,
        hunk_applicator: HunkApplying,
    ) -> None:
        self._format_parser = format_parser
        self._content_extractor = content_extractor
        self._hunk_applicator = hunk_applicator

    def parse(self, command: str) -> list:
        return self._format_parser.parse(command)

    def add_content(self, lines: list) -> str:
        return self._content_extractor.add_content(lines)

    def apply_update(self, existing_content: str, body_lines: list) -> str:
        return self._hunk_applicator.apply_update(existing_content, body_lines)
