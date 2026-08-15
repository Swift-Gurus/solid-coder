"""Defines typed condition declaration evaluation."""

from __future__ import annotations

from typing import Any, Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.condition_runtime import ConditionRuntime


"""
solid-name: ConditionEvaluating
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for dispatching one typed condition through its comparison runtime.
"""
class ConditionEvaluating(Protocol):
    def evaluate(
        self,
        condition: ConditionDeclaration,
        runtime: ConditionRuntime,
        context: dict[str, Any],
    ) -> bool: ...
