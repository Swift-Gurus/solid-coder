"""
solid-description: Extracts only the changed line ranges from a before/after text pair.
solid-category: service
solid-tags: [hook, utility]
"""

import difflib


class DiffChunker:
    """Extracts only the changed lines from a before/after text pair."""

    def chunk(self, old_content: str, new_content: str) -> tuple:
        """Return (old_changed, new_changed) containing only lines that differ."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        old_changed, new_changed = [], []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines).get_opcodes():
            if tag == "equal":
                continue
            old_changed.extend(old_lines[i1:i2])
            new_changed.extend(new_lines[j1:j2])
        return "\n".join(old_changed), "\n".join(new_changed)
