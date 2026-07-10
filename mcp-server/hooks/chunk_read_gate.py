"""
solid-description: Validates commands to ensure file operations use designated access methods.
solid-category: service
solid-tags: [hook]
"""

import re
from typing import Optional


class ChunkReadGate:
    """Detects Bash commands that read MCP chunk files instead of using the Read tool."""

    # Chunk files are named: solid-coder-{prefix}-{timestamp}-{n}of{total}.md
    _CHUNK_RE = re.compile(r'solid-coder-\S+-\d+-\d+of\d+\.md')
    _MSG = (
        "[chunk-read-gate] MCP chunk files must be read with the Read tool, not Bash. "
        "The MCP returned multiple chunk paths and instructed you to read each one "
        "in order using the Read tool. Using Bash (cat, head, tail, etc.) truncates "
        "or skips chunks. Use the Read tool on each path listed in the MCP response."
    )

    def check(self, command: str) -> Optional[str]:
        """Return the block message if command references an MCP chunk file, else None."""
        return self._MSG if self._CHUNK_RE.search(command) else None
