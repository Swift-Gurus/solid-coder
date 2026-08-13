"""Classifies paths declared by workflow resource fields."""

from pathlib import Path

from harness.workflow_resource_path_classification import WorkflowResourcePathClassification
from harness.workflow_resource_reference_kind import WorkflowResourceReferenceKind


"""
solid-name: WorkflowResourcePathClassifier
solid-category: service
solid-spec: [SPEC-035]
solid-description: Identifies the resolution anchor and normalized path represented by a workflow resource declaration.
"""
class WorkflowResourcePathClassifier:
    _PACKAGE_PREFIX = "$package/"

    def classify(self, declared_value: str) -> WorkflowResourcePathClassification:
        raw_path = Path(declared_value)
        if raw_path.is_absolute():
            return WorkflowResourcePathClassification(
                path=raw_path,
                kind=WorkflowResourceReferenceKind.ABSOLUTE,
            )
        if declared_value.startswith(self._PACKAGE_PREFIX):
            return WorkflowResourcePathClassification(
                path=Path(declared_value.removeprefix(self._PACKAGE_PREFIX)),
                kind=WorkflowResourceReferenceKind.PACKAGE_ROOT,
            )
        if raw_path.name == declared_value:
            return WorkflowResourcePathClassification(
                path=raw_path,
                kind=WorkflowResourceReferenceKind.CONVENTIONAL_PACKAGE_DIRECTORY,
            )
        return WorkflowResourcePathClassification(
            path=raw_path,
            kind=WorkflowResourceReferenceKind.DECLARING_FILE,
        )
