"""Defines a named project configuration section read."""

from pathlib import Path
from typing import Protocol

"""
solid-name: ConfigSectionReading
solid-category: abstraction
solid-spec: [SPEC-069]
solid-description: Contract for reading an effective named configuration section for a project directory.
"""


class ConfigSectionReading(Protocol):
    def __call__(self, section: str, *, _cwd: Path | None = None) -> dict: ...
