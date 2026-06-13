"""
solid-description: Recursively merges two config dicts with child-wins-per-key semantics.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Protocol


class ConfigMerging(Protocol):
    def merge(self, base: dict, override: dict) -> dict: ...


class ConfigMerger:
    """Partial merge: override wins key-by-key, nested dicts merged recursively."""

    def merge(self, base: dict, override: dict) -> dict:
        result = dict(base)
        for key, val in override.items():
            if isinstance(val, dict) and isinstance(result.get(key), dict):
                result[key] = self.merge(result[key], val)
            else:
                result[key] = val
        return result
