"""Defines the supported workflow resource reference anchors."""

from enum import Enum


"""
solid-name: WorkflowResourceReferenceKind
solid-category: model
solid-spec: [SPEC-035]
solid-description: Enumerates the resolved anchor semantics parsed from a workflow resource reference.
"""
class WorkflowResourceReferenceKind(str, Enum):
    DECLARING_FILE = "declaring_file"
    PACKAGE_ROOT = "package_root"
    CONVENTIONAL_PACKAGE_DIRECTORY = "conventional_package_directory"
    ABSOLUTE = "absolute"
