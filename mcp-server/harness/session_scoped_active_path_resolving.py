"""
solid-name: SessionScopedActivePathResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for resolving an active path within a session scope.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class SessionScopedActivePathResolving(Protocol):

    def resolve(self, base_dir: Path) -> Path: ...
