"""Defines lookup of logical operation registrations."""

from typing import Protocol

from harness.operation_registration import OperationRegistration


"""
solid-name: OperationRegistrationResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for resolving typed operation registrations by logical name.
"""
class OperationRegistrationResolving(Protocol):
    def resolve(self, name: str) -> OperationRegistration: ...
