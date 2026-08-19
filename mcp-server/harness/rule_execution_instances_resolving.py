"""Defines resolution of executable rule instances from terminal run state."""

from typing import Protocol

from harness.flow_def import FlowDef
from harness.rule_execution_instance import RuleExecutionInstance
from harness.run_state import RunState


"""
solid-name: RuleExecutionInstancesResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving completed root and included rule instances in stable workflow execution order.
"""
class RuleExecutionInstancesResolving(Protocol):
    def resolve(
        self,
        flow_def: FlowDef,
        run_state: RunState,
        root_instance_id: str,
    ) -> list[RuleExecutionInstance]: ...
