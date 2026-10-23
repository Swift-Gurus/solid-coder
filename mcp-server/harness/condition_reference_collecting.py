"""Defines typed workflow condition reference collection."""

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.workflow_expression import WorkflowExpression

"""
solid-name: ConditionReferenceCollecting
solid-category: abstraction
solid-spec: [SPEC-053]
solid-description: Contract for collecting authored references from a typed workflow condition.
"""


class ConditionReferenceCollecting(Protocol):
    def collect(
        self,
        condition: ConditionDeclaration,
    ) -> list[WorkflowExpression]: ...
