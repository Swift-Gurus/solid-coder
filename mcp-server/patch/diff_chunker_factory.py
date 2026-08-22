"""Composes changed-content selection."""

import difflib

from diff_chunker import DiffChunker


"""
solid-name: DiffChunkerFactory
solid-category: factory
solid-description: Configures changed-content selection for prospective source revisions.
solid-tags: [hook, utility]
"""
class DiffChunkerFactory:
    def make(self) -> DiffChunker:
        return DiffChunker(
            opcode_resolver=lambda previous, prospective: (
                difflib.SequenceMatcher(
                    None,
                    previous,
                    prospective,
                ).get_opcodes()
            )
        )
