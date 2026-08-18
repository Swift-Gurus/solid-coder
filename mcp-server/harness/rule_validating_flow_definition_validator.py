"""Adds executable-rule validation to an existing workflow validator."""

from harness.flow_def import FlowDef
from harness.flow_definition_validating import FlowDefinitionValidating
from harness.rule_workflow_validating import RuleWorkflowValidating


"""
solid-name: RuleValidatingFlowDefinitionValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Decorates workflow validation with rule-structure checks while preserving existing lifecycle validation.
"""
class RuleValidatingFlowDefinitionValidator(FlowDefinitionValidating):
    def __init__(
        self,
        delegate: FlowDefinitionValidating,
        rule_validator: RuleWorkflowValidating,
    ) -> None:
        self._delegate = delegate
        self._rule_validator = rule_validator

    def validate_resolved(self, definition: FlowDef) -> None:
        self._rule_validator.validate(definition)
        self._delegate.validate_resolved(definition)

    def validate_assembled(self, flow: FlowDef) -> None:
        self._delegate.validate_assembled(flow)
