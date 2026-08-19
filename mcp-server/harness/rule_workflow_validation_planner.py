"""Partitions resolved workflow steps by typed rule ownership."""

from harness.flow_def import FlowDef
from harness.rule_workflow_validation_plan import RuleWorkflowValidationPlan
from harness.rule_workflow_validation_planning import RuleWorkflowValidationPlanning
from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope


"""
solid-name: RuleWorkflowValidationPlanner
solid-category: service
solid-spec: [SPEC-039]
solid-description: Partitions root and included workflow steps into ordered rule-validation scopes without losing ownership.
"""
class RuleWorkflowValidationPlanner(RuleWorkflowValidationPlanning):
    def resolve(self, definition: FlowDef) -> RuleWorkflowValidationPlan:
        included_rule_groups = [
            group
            for group in definition.alias_groups
            if group.rule_workflow is not None
        ]
        included_rule_step_ids = {
            member_id
            for group in included_rule_groups
            for member_id in group.member_ids
        }
        root_steps = [
            step
            for step in definition.step_declarations
            if step.id not in included_rule_step_ids
        ]
        scopes: list[RuleWorkflowValidationScope] = []
        if definition.rule is not None:
            scopes.append(RuleWorkflowValidationScope(
                workflow_id=definition.workflow_id,
                declaration=definition.rule,
                steps=root_steps,
            ))

        for group in included_rule_groups:
            rule_workflow = group.rule_workflow
            if rule_workflow is None:
                continue
            scopes.append(RuleWorkflowValidationScope(
                workflow_id=rule_workflow.workflow_id,
                declaration=rule_workflow.declaration,
                steps=[
                    step
                    for step in definition.step_declarations
                    if step.id in group.member_ids
                ],
            ))

        return RuleWorkflowValidationPlan(
            scopes=scopes,
            unowned_steps=(
                []
                if definition.rule is not None
                else [
                    step
                    for step in root_steps
                    if step.type in {"metric", "exception"}
                ]
            ),
        )
