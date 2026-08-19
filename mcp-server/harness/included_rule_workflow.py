"""Defines the identity and declaration of one included review rule workflow."""

from pydantic import BaseModel, ConfigDict

from harness.rule_declaration import RuleDeclaration


"""
solid-name: IncludedRuleWorkflow
solid-category: model
solid-spec: [SPEC-039]
solid-description: Preserves typed rule ownership when a catalog rule is included in a composite workflow.
"""
class IncludedRuleWorkflow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str
    declaration: RuleDeclaration
