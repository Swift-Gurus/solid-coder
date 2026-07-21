"""
solid-name: StartupContext
solid-category: model
solid-spec: [SPEC-013]
solid-description: Context providing startup configuration and environment information for flow initialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class StartupContext:
    detected_env: str
    base_dir: Path
    search_paths: list[str] = field(default_factory=list)
