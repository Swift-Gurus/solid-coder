"""Resolves and contains paths declared by workflow resources."""

from __future__ import annotations

from pathlib import Path

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.workflow_package_root_locating import WorkflowPackageRootLocating
from harness.workflow_resource_reference import WorkflowResourceReference
from harness.workflow_resource_reference_kind import WorkflowResourceReferenceKind


"""
solid-name: WorkflowResourcePathResolver
solid-category: service
solid-spec: [SPEC-035]
solid-description: Resolves declaring-file-relative resources while containing packaged references.
"""
class WorkflowResourcePathResolver:

    def __init__(
        self,
        package_root_locator: WorkflowPackageRootLocating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._package_root_locator = package_root_locator
        self._error_factory = error_factory

    def resolve(
        self,
        declaring_file: Path,
        reference: WorkflowResourceReference,
    ) -> Path:
        declaring = declaring_file.resolve()
        package_root = self._package_root_locator.locate(declaring)

        if reference.kind == WorkflowResourceReferenceKind.PACKAGE_ROOT:
            if package_root is None:
                raise self._error_factory.create(
                    f"Workflow resource '{reference.declared_value}' requires an owning package"
                )
            candidate = (package_root / reference.path).resolve()
        elif reference.kind == WorkflowResourceReferenceKind.CONVENTIONAL_PACKAGE_DIRECTORY:
            candidate = (
                package_root / reference.conventional_directory.value / reference.path
                if package_root is not None
                else declaring.parent / reference.path
            ).resolve()
        elif reference.kind == WorkflowResourceReferenceKind.ABSOLUTE:
            candidate = reference.path.resolve()
        else:
            candidate = (declaring.parent / reference.path).resolve()

        if package_root is not None and not candidate.is_relative_to(package_root.resolve()):
            raise self._error_factory.create(
                f"Workflow resource '{reference.declared_value}' escapes package root '{package_root}'"
            )
        return candidate
