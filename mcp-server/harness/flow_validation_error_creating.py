"""Defines creation of workflow validation failures."""

from __future__ import annotations

from typing import Protocol

from harness.flow_validation_error import FlowValidationError


"""
solid-name: FlowValidationErrorCreating
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for creating an actionable workflow validation failure from a message.
"""
class FlowValidationErrorCreating(Protocol):
    def create(self, message: str) -> FlowValidationError: ...
