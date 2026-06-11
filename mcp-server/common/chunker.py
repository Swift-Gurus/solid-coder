#!/usr/bin/env python3
"""
solid-description: Utility that transparently handles oversized text and JSON responses by offloading large content to external storage and returning retrieval instructions.
solid-category: utility
solid-tags: [utility, service]
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any

CHUNK_SIZE = 40_000


class Chunker:
    """Splits oversized content into temp files and returns Read instructions.

    Instantiate with a custom chunk_size for testing. The default matches
    the historical CHUNK_SIZE constant used across all MCP servers.
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE) -> None:
        self._chunk_size = chunk_size

    def chunk(self, content: str, prefix: str) -> str:
        """Return content directly if small enough, otherwise save to chunk files.

        When content exceeds chunk_size characters, writes numbered files to /tmp
        and returns instructions for the agent to read them with the Read tool.
        """
        if len(content) <= self._chunk_size:
            return content

        ts = int(time.time())
        chunks = [content[i:i + self._chunk_size] for i in range(0, len(content), self._chunk_size)]
        paths = []
        for n, part in enumerate(chunks, 1):
            path = self._make_temp_path(prefix, ts, f"-{n}of{len(chunks)}")
            path.write_text(part, encoding="utf-8")
            paths.append(str(path))

        lines = [
            f"Content is large ({len(content):,} chars across {len(chunks)} chunks).",
            "MANDATORY: you MUST read ALL chunk files below using the Read tool before",
            "doing anything else. Do NOT use Bash. Do NOT proceed until every chunk is read.",
            "The pre-tool hook will block any non-Read action until all chunks are consumed.",
            "",
        ] + [f"- {p}" for p in paths]
        return "\n".join(lines)

    def save_json(self, data: Any, prefix: str) -> Any:
        """Return data directly if JSON is small enough, otherwise save to a temp file.

        When the serialized JSON exceeds chunk_size characters, writes a single .json
        temp file and returns an instruction dict for the agent to read it.
        """
        serialized = json.dumps(data, indent=2)
        if len(serialized) <= self._chunk_size:
            return data
        ts = int(time.time())
        path = self._make_temp_path(prefix, ts).with_suffix(".json")
        path.write_text(serialized, encoding="utf-8")
        return {
            "large_output": True,
            "chars": len(serialized),
            "file": str(path),
            "instruction": (
                f"Output is large ({len(serialized):,} chars). "
                f"Read the file at '{path}' using the Read tool."
            ),
        }

    def _make_temp_path(self, prefix: str, ts: int, suffix: str = "") -> Path:
        name = f"solid-coder-{prefix}-{ts}{suffix}.md"
        return Path(tempfile.gettempdir()) / name
