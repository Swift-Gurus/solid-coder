"""
solid-description: Extracts only the changed line ranges from a before/after text pair.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Callable

from changed_content import ChangedContent

"""
solid-name: DiffChunker
solid-category: service
solid-description: Selects changed portions from previous and prospective source content.
solid-tags: [hook, utility]
"""
class DiffChunker:
    """Extracts only the changed lines from a before/after text pair."""

    def __init__(self, opcode_resolver: Callable) -> None:
        self._opcode_resolver = opcode_resolver

    def chunk(self, old_content: str, new_content: str) -> ChangedContent:
        """Return (old_changed, new_changed) containing only lines that differ."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        old_changed, new_changed = [], []
        for tag, i1, i2, j1, j2 in self._opcode_resolver(old_lines, new_lines):
            if tag == "equal":
                continue
            old_changed.extend(old_lines[i1:i2])
            new_changed.extend(new_lines[j1:j2])
        return ChangedContent(
            previous="\n".join(old_changed),
            prospective="\n".join(new_changed),
        )
