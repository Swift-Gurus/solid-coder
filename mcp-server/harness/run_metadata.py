"""
solid-name: RunMetadata
solid-category: model
solid-spec: [SPEC-013]
solid-description: Contains the parameters and detected environment for a run.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunMetadata:
    params: dict
    detected_env: str
