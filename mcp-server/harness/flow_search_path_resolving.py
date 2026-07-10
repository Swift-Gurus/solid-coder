"""
solid-name: FlowSearchPathResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for resolving an ordered list of flow search paths, with project taking precedence over plugin sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FlowSearchPathResolving(Protocol):

    def resolve(self) -> list[Path]: ...
