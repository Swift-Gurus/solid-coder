"""Creates typed workflow resource references."""

from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_path_classifying import WorkflowResourcePathClassifying
from harness.workflow_resource_reference import WorkflowResourceReference


"""
solid-name: WorkflowResourceReferenceFactory
solid-category: factory
solid-spec: [SPEC-035]
solid-description: Creates workflow resource references from declared values and classified resolution locations.
"""
class WorkflowResourceReferenceFactory:
    def __init__(
        self,
        path_classifier: WorkflowResourcePathClassifying,
        conventional_directory: WorkflowResourceDirectory,
    ) -> None:
        self._path_classifier = path_classifier
        self._conventional_directory = conventional_directory

    def create(self, declared_value: str) -> WorkflowResourceReference:
        classification = self._path_classifier.classify(declared_value)
        return WorkflowResourceReference(
            declared_value=declared_value,
            path=classification.path,
            kind=classification.kind,
            conventional_directory=self._conventional_directory,
        )
