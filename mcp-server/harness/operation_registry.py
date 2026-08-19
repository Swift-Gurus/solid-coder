"""Indexes internal workflow operations by stable logical name."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.logical_operation_name_validating import (
    LogicalOperationNameValidating,
)
from harness.operation_registration import OperationRegistration


"""
solid-name: OperationRegistry
solid-category: service
solid-spec: [SPEC-010, SPEC-040]
solid-description: Resolves unique typed operation registrations by validated logical name.
"""
class OperationRegistry:
    def __init__(
        self,
        registrations: list[OperationRegistration],
        name_validator: LogicalOperationNameValidating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._registrations = registrations
        self._name_validator = name_validator
        self._error_factory = error_factory
        self._validate_registrations()

    def resolve(self, name: str) -> OperationRegistration:
        self._validate_name(name)
        for registration in self._registrations:
            if registration.name == name:
                return registration
        raise self._error_factory.create(f"Unknown logical operation '{name}'")

    def _validate_registrations(self) -> None:
        names: set[str] = set()
        for registration in self._registrations:
            self._validate_name(registration.name)
            if registration.name in names:
                raise self._error_factory.create(
                    f"Duplicate logical operation '{registration.name}'"
                )
            names.add(registration.name)

    def _validate_name(self, name: str) -> None:
        if not self._name_validator.is_valid(name):
            raise self._error_factory.create(
                f"'{name}' is not a valid logical operation; expected namespace.name"
            )
