"""
solid-description: Shared prompt-building infrastructure — file-based reader and base builder used by health check and frontmatter correction.
solid-category: utility
solid-tags: [hook]
"""

from pathlib import Path
from typing import Optional, Protocol

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SHARED_PROMPTS_DIR = PLUGIN_ROOT / "mcp-server" / "prompts"


class PromptReading(Protocol):
    def read(self, filename: str) -> str: ...


class FilePromptReader:
    """Reads prompt fragment files from a directory on disk."""

    def __init__(self, prompts_dir: Path = SHARED_PROMPTS_DIR) -> None:
        self._dir = prompts_dir

    def read(self, filename: str) -> str:
        return (self._dir / filename).read_text(encoding="utf-8").rstrip()


class BasePromptBuilder:
    """Shared infrastructure for file-based LLM prompt builders.

    Provides injected readers, a spawned-by header, and per-file read helpers.
    Subclasses implement build() using these primitives.
    """

    def __init__(
        self,
        reader: Optional[PromptReading] = None,
        shared_reader: Optional[PromptReading] = None,
        prompts_dir: Optional[Path] = None,
    ) -> None:
        self._reader = reader or FilePromptReader(
            prompts_dir=prompts_dir or SHARED_PROMPTS_DIR
        )
        self._shared = shared_reader or FilePromptReader(prompts_dir=SHARED_PROMPTS_DIR)

    def _header(self, parent_session_id: str) -> str:
        return f"# spawned-by: {parent_session_id}\n\n" if parent_session_id else ""

    def _read(self, filename: str) -> str:
        return self._reader.read(filename)

    def _read_shared(self, filename: str) -> str:
        return self._shared.read(filename)
