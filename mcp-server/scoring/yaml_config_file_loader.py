"""
solid-description: Loads a configuration file from a path and returns it as a dictionary, or None if loading fails.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional, Protocol

from scoring.yaml_loader import YamlLoading


class ConfigFileLoading(Protocol):
    def load(self, path: Path) -> Optional[dict]: ...


class YamlConfigFileLoader:
    """Reads a YAML file and returns its content as a dict, or None on any failure."""

    def __init__(self, loader: YamlLoading) -> None:
        self._loader = loader

    def load(self, path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        try:
            result = self._loader.safe_load(path.read_text(encoding="utf-8"))
            return result if isinstance(result, dict) else None
        except Exception:
            return None
