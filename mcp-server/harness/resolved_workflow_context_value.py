"""Defines the presence and value of a typed workflow-context lookup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


Value = TypeVar("Value")


"""
solid-name: ResolvedWorkflowContextValue
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Preserves absent-versus-present-null semantics for a typed workflow runtime value.
"""
@dataclass(frozen=True)
class ResolvedWorkflowContextValue(Generic[Value]):
    present: bool
    value: Value | None = None
