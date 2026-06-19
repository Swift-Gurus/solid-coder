"""
solid-description: Manages creation, reading, and cleanup of temporary files.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HOOKS_DIR = Path(__file__).resolve().parents[3] / 'hooks'
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional


class _TempPathProvider:
    """Private helper: creates uniquely named temp file paths."""

    def __init__(self, path_factory: Callable[[str], Path]) -> None:
        self._factory = path_factory

    def prompt(self) -> Path:
        return self._factory("prompt")

    def result(self) -> Path:
        return self._factory("result")


class _TempFileIO:
    """Private helper: handles open/read/cleanup of temp files."""

    @contextmanager
    def stdin(self, path: Path):
        with open(path, encoding="utf-8") as fh:
            yield fh

    def read(self, path: Path) -> Optional[str]:
        return path.read_text(encoding="utf-8").strip() if path.exists() else None

    def unlink(self, *paths: Path) -> None:
        for p in paths:
            p.unlink(missing_ok=True)


def _uuid_temp_path(prefix: str) -> Path:
    return Path(tempfile.gettempdir()) / f"codex-{prefix}-{uuid.uuid4()}.txt"


class CodexTempFileManager:
    """Facade: delegates temp-file path creation and I/O to private helpers."""

    def __init__(self, path_factory: Callable[[str], Path] = _uuid_temp_path) -> None:
        self._paths = _TempPathProvider(path_factory)
        self._io = _TempFileIO()

    def write_prompt(self, prompt: str) -> Path:
        p = self._paths.prompt()
        p.write_text(prompt, encoding="utf-8")
        return p

    def result_path(self) -> Path:
        return self._paths.result()

    def prompt_stdin(self, path: Path):
        return self._io.stdin(path)

    def read_result(self, path: Path) -> Optional[str]:
        return self._io.read(path)

    def cleanup(self, *paths: Path) -> None:
        self._io.unlink(*paths)
