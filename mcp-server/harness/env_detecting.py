"""
solid-name: EnvDetecting
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for detecting runtime environment configuration as a string.
"""

from __future__ import annotations

from typing import Protocol


class EnvDetecting(Protocol):

    def detect(self) -> str: ...
