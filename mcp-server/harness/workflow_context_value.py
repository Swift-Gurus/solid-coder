"""Defines one typed named value available to workflow expression evaluation."""

from dataclasses import dataclass
from typing import Generic, TypeVar


Value = TypeVar("Value")


"""
solid-name: WorkflowContextValue
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates a workflow runtime context name with its typed or schema-backed value.
"""
@dataclass(frozen=True)
class WorkflowContextValue(Generic[Value]):
    name: str
    value: Value
