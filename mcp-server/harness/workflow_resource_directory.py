"""Defines conventional directories for packaged workflow resources."""

from enum import Enum


"""
solid-name: WorkflowResourceDirectory
solid-category: model
solid-spec: [SPEC-035]
solid-description: Enumerates the conventional package directory assigned to each workflow resource field.
"""
class WorkflowResourceDirectory(str, Enum):
    PROMPTS = "prompts"
    SCHEMAS = "schemas"
    STEPS = "steps"
    SUBFLOWS = "subflows"
    SCRIPTS = "scripts"
