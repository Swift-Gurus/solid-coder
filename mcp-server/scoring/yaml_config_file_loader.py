"""
solid-description: Loads a configuration file from a path and returns it as a dictionary, or None if loading fails.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Protocol

from logging_protocol import Logging

from scoring.yaml_loader import YamlLoading


class ConfigFileLoading(Protocol):
    def load(self, path: Path) -> dict | None: ...


class YamlConfigFileLoader:
    """Reads a YAML file and returns its content as a dict, or None on any failure."""

    def __init__(self, loader: YamlLoading, logger: Logging) -> None:
        self._loader = loader
        self._logger = logger

    def load(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            result = self._loader.safe_load(path.read_text(encoding="utf-8"))
            return result if isinstance(result, dict) else None
        except Exception as exc:  # noqa: BLE001 — Log configuration-load failures and return unavailable content for callers to handle.
            self._logger.log(
                f"Configuration loading failed: path={path}; {type(exc).__name__}: {exc}"
            )
            return None
