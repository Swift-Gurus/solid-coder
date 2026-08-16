"""Defines conversion from named boundary values to typed workflow context values."""

from collections.abc import Mapping
from typing import Protocol, TypeVar

from harness.workflow_context_values import WorkflowContextValues


Value = TypeVar("Value")


"""
solid-name: WorkflowContextValuesMapping
solid-category: abstraction
solid-spec: [SPEC-031, SPEC-037]
solid-description: Contract for mapping named boundary values into typed workflow context values.
"""
class WorkflowContextValuesMapping(Protocol):
    def map(
        self,
        values: Mapping[str, Value],
    ) -> WorkflowContextValues[Value]: ...
