"""
solid-description: Validates whether a session stop is permitted.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_SESSION_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _SESSION_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


class RegistryAccessing(Protocol):
    def get_entry(self, session_id: str, cwd: str) -> Optional[dict]: ...
    def deregister(self, session_id: str, cwd: str) -> None: ...


class ToolChecking(Protocol):
    def check(self, transcript_path: Optional[str], session_type: str) -> dict: ...


class SessionStopValidator:
    """Facade: validates session stop by delegating to registry and tool-call checker."""

    def __init__(self, registry: RegistryAccessing, checker: ToolChecking) -> None:
        self._registry = registry
        self._checker = checker

    def validate(self, session_id: str, transcript_path: Optional[str], cwd: str) -> dict:
        entry = self._registry.get_entry(session_id, cwd)
        if not entry:
            return {"allow": True}
        result = self._checker.check(transcript_path, entry.get("type", ""))
        if result.get("allow"):
            self._registry.deregister(session_id, cwd)
        return result
