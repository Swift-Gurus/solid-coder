"""Locates package ownership for workflow resources."""

from __future__ import annotations

from pathlib import Path


"""
solid-name: WorkflowPackageRootLocator
solid-category: service
solid-spec: [SPEC-035]
solid-description: Locates the nearest workflow.yaml ancestor owning a declaring resource file.
"""
class WorkflowPackageRootLocator:
    def locate(self, declaring_file: Path) -> Path | None:
        current = declaring_file.resolve().parent
        for candidate in (current, *current.parents):
            if (candidate / "workflow.yaml").is_file():
                return candidate
        return None
