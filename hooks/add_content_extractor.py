""" 
solid-description: Reconstructs file content by removing the leading character from formatted lines.
solid-category: service
solid-tags: [hook, utility]
"""


class AddContentExtractor:
    """Extracts the complete new-file content from Apply Patch Add File body lines."""

    def add_content(self, lines: list) -> str:
        """Strip the leading '+' from each Add File body line and join into file content."""
        return "\n".join(self._strip_prefix(l) for l in lines if l.startswith("+"))

    def _strip_prefix(self, line: str) -> str:
        return line[1:] if len(line) > 1 else ""
