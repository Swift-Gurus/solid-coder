"""Selects reviewable entries from a parsed patch command."""

from patch_parsing import PatchParsing


"""
solid-name: PatchEntrySelector
solid-category: service
solid-description: Selects every file change requiring content review while excluding removals.
solid-tags: [hook]
"""
class PatchEntrySelector:
    def __init__(self, parser: PatchParsing) -> None:
        self._parser = parser

    def select(self, command: str) -> list[dict]:
        return [
            entry
            for entry in self._parser.parse(command)
            if entry["operation"] != "delete"
        ]
