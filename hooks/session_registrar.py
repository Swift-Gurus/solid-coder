"""
solid-description: Registers managed LLM sessions in a project-local registry.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from session_store import StoreAccessing  # noqa: E402


class SessionRegistrar:
    """Records a new managed LLM session in the project-local registry."""

    def __init__(self, store: StoreAccessing) -> None:
        self._store = store

    def register(self, session_id: str, session_type: str, cwd: str) -> dict:
        path = self._store.registry_path(cwd)
        registry = self._store.load(path)
        registry[session_id] = {
            "type": session_type,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store.save(path, registry)
        return {"registered": True, "session_id": session_id, "type": session_type}
