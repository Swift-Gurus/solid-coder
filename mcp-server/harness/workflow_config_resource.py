"""Defines one resolved YAML or JSON workflow resource."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: WorkflowConfigResource
solid-category: model
solid-spec: [SPEC-035]
solid-description: Represents loaded structured workflow content and its resolved source path.
"""
@dataclass(frozen=True)
class WorkflowConfigResource:
    path: Path
    content: dict
