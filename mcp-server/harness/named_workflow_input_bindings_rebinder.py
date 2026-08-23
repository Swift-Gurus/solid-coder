"""Rebinds one workflow input to another authored input expression."""

from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_input_bindings_rebinding import (
    WorkflowInputBindingsRebinding,
)


"""
solid-name: NamedWorkflowInputBindingsRebinder
solid-category: service
solid-spec: [SPEC-037, SPEC-039]
solid-description: Replaces a selected input expression with the expression carried by another named input binding.
"""
class NamedWorkflowInputBindingsRebinder(WorkflowInputBindingsRebinding):
    def __init__(self, source_name: str, target_name: str) -> None:
        self._source_name = source_name
        self._target_name = target_name

    def rebind(
        self,
        bindings: list[WorkflowInputBinding],
    ) -> list[WorkflowInputBinding]:
        source = next(
            (
                binding
                for binding in bindings
                if binding.name == self._source_name
            ),
            None,
        )
        if source is None:
            return bindings
        return [
            WorkflowInputBinding(
                name=binding.name,
                expression=source.expression,
            )
            if binding.name == self._target_name
            else binding
            for binding in bindings
        ]
