"""
solid-name: RunsBaseDirResolving
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for resolving the runs base directory path for a project.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class RunsBaseDirResolving(Protocol):

    def resolve(self) -> Path: ...
