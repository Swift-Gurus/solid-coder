"""Resolves and contains paths declared by workflow resources."""

from __future__ import annotations

from pathlib import Path

from harness.models import FlowValidationError
from harness.workflow_package_root_locating import WorkflowPackageRootLocating


"""
solid-name: WorkflowResourcePathResolver
solid-category: service
solid-spec: [SPEC-035]
solid-description: Resolves declaring-file-relative resources while containing packaged references.
"""
class WorkflowResourcePathResolver:

    def __init__(self, package_root_locator: WorkflowPackageRootLocating) -> None:
        self._package_root_locator = package_root_locator

    def resolve(self, declaring_file: Path, reference: str) -> Path:
        declaring = declaring_file.resolve()
        raw_reference = Path(reference)
        candidate = (
            raw_reference.resolve()
            if raw_reference.is_absolute()
            else (declaring.parent / raw_reference).resolve()
        )
        package_root = self._package_root_locator.locate(declaring)
        if package_root is not None and not candidate.is_relative_to(package_root.resolve()):
            raise FlowValidationError(
                f"Workflow resource '{reference}' escapes package root '{package_root}'"
            )
        return candidate
