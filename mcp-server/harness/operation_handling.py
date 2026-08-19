"""Defines typed execution for one internal workflow operation."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

OperationInput = TypeVar("OperationInput", bound=BaseModel)
OperationOutput = TypeVar("OperationOutput", bound=BaseModel)


"""
solid-name: OperationHandling
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for executing typed internal workflow operations.
"""
class OperationHandling(
    Protocol,
    Generic[OperationInput, OperationOutput],
):
    def execute(self, operation_input: OperationInput) -> OperationOutput: ...
