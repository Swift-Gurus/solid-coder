"""
solid-description: Protocol and implementation for loading YAML text with graceful fallback support.
solid-category: utility
solid-tags: [utility]
"""

from typing import Any, Optional, Protocol

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _yaml = None  # type: ignore[assignment]
    _YAML_AVAILABLE = False


class YamlLoading(Protocol):
    def safe_load(self, text: str) -> Any: ...


class PyYamlLoader:
    """Concrete YAML loader — wraps yaml.safe_load, returns None when PyYAML is absent."""

    def safe_load(self, text: str) -> Any:
        if not _YAML_AVAILABLE:
            return None
        return _yaml.safe_load(text)
