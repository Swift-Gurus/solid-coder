"""Defines structural validation of one executable rule workflow."""

from typing import Protocol

from harness.metric_declaration import MetricDeclaration
from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope


"""
solid-name: RuleWorkflowStructureValidating
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-044]
solid-description: Contract for validating one rule execution shape and returning its typed metric declarations.
"""
class RuleWorkflowStructureValidating(Protocol):
    def validate(
        self,
        scope: RuleWorkflowValidationScope,
    ) -> list[MetricDeclaration]: ...
