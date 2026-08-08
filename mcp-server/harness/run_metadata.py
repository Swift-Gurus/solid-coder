"""
solid-name: RunMetadata
solid-category: model
solid-spec: [SPEC-031]
solid-description: Represents metadata for a run execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunMetadata:
    params: dict