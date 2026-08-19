"""Associates one logical operation name with its typed contract and handler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Type, TypeVar

from pydantic import BaseModel

from harness.operation_handling import OperationHandling

OperationInput = TypeVar("OperationInput", bound=BaseModel)
OperationOutput = TypeVar("OperationOutput", bound=BaseModel)


"""
solid-name: OperationRegistration
solid-category: model
solid-spec: [SPEC-010, SPEC-040]
solid-description: Carries one logical operation's typed input, output, and execution capability.
"""
@dataclass(frozen=True)
class OperationRegistration(Generic[OperationInput, OperationOutput]):
    name: str
    input_model: Type[OperationInput]
    output_model: Type[OperationOutput]
    handler: OperationHandling[OperationInput, OperationOutput]
