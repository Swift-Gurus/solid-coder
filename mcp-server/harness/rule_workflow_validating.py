"""Defines structural validation for executable review-rule workflows."""

from typing import Protocol

from harness.flow_def import FlowDef


"""
solid-name: RuleWorkflowValidating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for validating executable review-rule structure and metric identities.
"""
class RuleWorkflowValidating(Protocol):
    def validate(self, definition: FlowDef) -> None: ...
