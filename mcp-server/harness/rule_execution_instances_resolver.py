"""Resolves completed root and included rule executions in stable order."""

from dataclasses import replace

from harness.flow_def import FlowDef
from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.rule_execution_completion_evaluating import (
    RuleExecutionCompletionEvaluating,
)
from harness.rule_execution_instance import RuleExecutionInstance
from harness.rule_execution_instances_resolving import (
    RuleExecutionInstancesResolving,
)
from harness.run_state import RunState


"""
solid-name: RuleExecutionInstancesResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Resolves completed root and included rule executions with stable workflow, instance, and step ownership.
"""
class RuleExecutionInstancesResolver(RuleExecutionInstancesResolving):
    def __init__(
        self,
        completion_evaluator: RuleExecutionCompletionEvaluating,
    ) -> None:
        self._completion_evaluator = completion_evaluator

    def resolve(
        self,
        flow_def: FlowDef,
        run_state: RunState,
        root_instance_id: str,
    ) -> list[RuleExecutionInstance]:
        instances: list[RuleExecutionInstance] = []
        if flow_def.rule is not None:
            instances.append(RuleExecutionInstance(
                workflow=IncludedRuleWorkflow(
                    workflow_id=flow_def.workflow_id,
                    declaration=flow_def.rule,
                ),
                instance_id=root_instance_id,
                steps=[
                    step
                    for step in flow_def.steps
                    if step.workflow_instance is None
                    or step.workflow_instance.rule_workflow is None
                ],
            ))

        for step in flow_def.steps:
            workflow_instance = step.workflow_instance
            if (
                workflow_instance is None
                or workflow_instance.rule_workflow is None
            ):
                continue
            existing_index = next(
                (
                    index
                    for index in range(len(instances))
                    if instances[index].instance_id
                    == workflow_instance.instance_id
                    and instances[index].workflow.workflow_id
                    == workflow_instance.rule_workflow.workflow_id
                ),
                None,
            )
            if existing_index is None:
                instances.append(RuleExecutionInstance(
                    workflow=workflow_instance.rule_workflow,
                    instance_id=workflow_instance.instance_id,
                    steps=[step],
                ))
            else:
                current = instances[existing_index]
                instances[existing_index] = replace(
                    current,
                    steps=[*current.steps, step],
                )

        return [
            instance
            for instance in instances
            if self._completion_evaluator.evaluate(instance, run_state)
        ]
