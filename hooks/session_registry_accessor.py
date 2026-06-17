"""
solid-description: Retrieves and removes session entries.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
from typing import Optional

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from session_store import StoreAccessing  # noqa: E402


class SessionRegistryAccessor:
    """Reads and removes session entries from the project registry file."""

    def __init__(self, store: StoreAccessing) -> None:
        self._store = store

    def get_entry(self, session_id: str, cwd: str) -> Optional[dict]:
        """Return the registry entry for session_id, or None if not registered."""
        path = self._store.registry_path(cwd)
        registry = self._store.load(path)
        return registry.get(session_id)

    def deregister(self, session_id: str, cwd: str) -> None:
        """Remove session_id from the registry."""
        path = self._store.registry_path(cwd)
        registry = self._store.load(path)
        registry.pop(session_id, None)
        self._store.save(path, registry)
