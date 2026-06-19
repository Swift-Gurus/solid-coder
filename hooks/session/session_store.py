"""
solid-description: Persists and retrieves session registry state.
solid-category: service
solid-tags: [hook, utility]
"""

import json
from pathlib import Path
from typing import Protocol

_REGISTRY_FILENAME = "active-sessions.json"


class StoreAccessing(Protocol):
    def registry_path(self, cwd: str) -> Path: ...
    def load(self, path: Path) -> dict: ...
    def save(self, path: Path, registry: dict) -> None: ...


class SessionStore:
    """Loads and saves the session registry JSON file for a project directory."""

    def registry_path(self, cwd: str) -> Path:
        slug = str(Path(cwd).resolve()).replace("/", "-")
        return Path.home() / ".solid-coder" / slug / _REGISTRY_FILENAME

    def load(self, path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, path: Path, registry: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(registry, indent=2), encoding="utf-8")