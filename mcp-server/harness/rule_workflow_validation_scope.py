"""Defines one rule workflow and the steps owned by its declaration."""

from dataclasses import dataclass

from harness.rule_declaration import RuleDeclaration
from harness.step_declaration import StepDeclaration


"""
solid-name: RuleWorkflowValidationScope
solid-category: model
solid-spec: [SPEC-039]
solid-description: Associates one rule identity and declaration with its owned workflow steps for structural validation.
"""
@dataclass(frozen=True)
class RuleWorkflowValidationScope:
    workflow_id: str
    declaration: RuleDeclaration
    steps: list[StepDeclaration]
