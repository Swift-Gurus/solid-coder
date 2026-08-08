"""
solid-name: FlowSearchPathResolving
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for resolving the client, plugin, package, and legacy workflow catalog roots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FlowSearchPathResolving(Protocol):

    def resolve(self) -> list[Path]: ...
