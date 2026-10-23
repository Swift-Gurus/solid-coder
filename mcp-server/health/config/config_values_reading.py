"""Defines a project-scoped configuration value read."""

from pathlib import Path
from typing import Protocol

"""
solid-name: ConfigValuesReading
solid-category: abstraction
solid-spec: [SPEC-069]
solid-description: Contract for reading effective configuration values for a project directory.
"""


class ConfigValuesReading(Protocol):
    def __call__(self, *, _cwd: Path | None = None) -> dict: ...
