"""Public API for session-scoped project context."""

from pathlib import Path

from session.project_context.directory_reader import (
    SessionProjectDirectoryReader,
    SessionProjectDirectoryReading,
)
from session.project_context.directory_recorder import (
    SessionProjectDirectoryRecorder,
    SessionProjectDirectoryRecording,
)
from session.project_context.path import (
    SessionProjectContextPathResolver,
    SessionProjectContextPathResolving,
)

DEFAULT_SESSION_ROOT: Path = Path.home() / ".solid-coder" / "sessions"

__all__ = [
    "DEFAULT_SESSION_ROOT",
    "SessionProjectContextPathResolver",
    "SessionProjectContextPathResolving",
    "SessionProjectDirectoryReader",
    "SessionProjectDirectoryReading",
    "SessionProjectDirectoryRecorder",
    "SessionProjectDirectoryRecording",
]
