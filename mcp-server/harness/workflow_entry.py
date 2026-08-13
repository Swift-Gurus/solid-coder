"""Defines the closed set of supported workflow entries."""

from typing import Union

from harness.inline_workflow_group import InlineWorkflowGroup
from harness.step_declaration import StepDeclaration
from harness.uses_workflow_entry import UsesWorkflowEntry
from harness.workflow_include_entry import WorkflowIncludeEntry


WorkflowEntry = Union[
    StepDeclaration,
    WorkflowIncludeEntry,
    UsesWorkflowEntry,
    InlineWorkflowGroup,
]
