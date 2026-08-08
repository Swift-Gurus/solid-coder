"""Defines discovery of workflow sources below one catalog root."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowSourceDiscovering
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for discovering packaged and legacy workflow sources below one root.
"""
class WorkflowSourceDiscovering(Protocol):
    def discover(self, root: Path) -> list[WorkflowSource]: ...
