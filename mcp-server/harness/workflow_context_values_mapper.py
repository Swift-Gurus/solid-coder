"""Maps named boundary values into typed workflow context values."""

from collections.abc import Mapping
from typing import TypeVar

from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_context_values_mapping import WorkflowContextValuesMapping


Value = TypeVar("Value")


"""
solid-name: WorkflowContextValuesMapper
solid-category: boundary
solid-spec: [SPEC-031, SPEC-037]
solid-description: Maps named boundary values into typed workflow context entries.
"""
class WorkflowContextValuesMapper(WorkflowContextValuesMapping):
    def map(
        self,
        values: Mapping[str, Value],
    ) -> WorkflowContextValues[Value]:
        return WorkflowContextValues(
            entries=[
                WorkflowContextValue(name=name, value=value)
                for name, value in values.items()
            ]
        )
