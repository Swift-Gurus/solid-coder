"""Defines decoding of authored internal operation steps."""

from typing import Protocol

from harness.operation_step_contract import OperationStepContract


"""
solid-name: OperationStepContractResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for decoding authored logical operation steps and registered outputs.
"""
class OperationStepContractResolving(Protocol):
    def resolve(self, raw: object) -> OperationStepContract: ...
