"""
solid-description: Applies patch updates to file content.
solid-category: service
solid-tags: [hook, utility]
"""


class HunkApplicator:
    """Applies apply_patch Update File diff hunks to produce post-apply file content."""

    def apply_update(self, existing_content: str, body_lines: list) -> str:
        """Apply Update File hunk lines to existing_content. Fails open on context mismatch."""
        file_lines = existing_content.splitlines()
        current_hunk: list = []
        for line in body_lines:
            if line.startswith("@@"):
                if current_hunk:
                    file_lines = self._apply_hunk(file_lines, current_hunk)
                current_hunk = []
            elif line != "*** End of File":
                current_hunk.append(line)
        if current_hunk:
            file_lines = self._apply_hunk(file_lines, current_hunk)
        return "\n".join(file_lines)

    def _apply_hunk(self, file_lines: list, hunk_lines: list) -> list:
        find_seg = [self._strip_prefix(l) for l in hunk_lines if l[:1] in (" ", "-")]
        replacement = [self._strip_prefix(l) for l in hunk_lines if l[:1] in (" ", "+")]
        if not find_seg:
            return file_lines + replacement
        n = len(find_seg)
        for i in range(len(file_lines) - n + 1):
            if file_lines[i:i + n] == find_seg:
                return file_lines[:i] + replacement + file_lines[i + n:]
        return file_lines

    def _strip_prefix(self, line: str) -> str:
        return line[1:] if len(line) > 1 else ""