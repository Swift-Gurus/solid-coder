"""
solid-name: EnvReading
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for reading a value from the process environment by key, with an optional default.
"""

from __future__ import annotations

from typing import Protocol


class EnvReading(Protocol):

    def get(self, key: str, default: str = "") -> str: ...