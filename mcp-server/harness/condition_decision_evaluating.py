"""Defines runtime workflow condition decisions."""

from __future__ import annotations

from typing import Any, Protocol

from harness.condition_declaration import ConditionDeclaration


"""
solid-name: ConditionDecisionEvaluating
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for evaluating one typed condition against runtime context.
"""
class ConditionDecisionEvaluating(Protocol):
    def evaluate(
        self,
        condition: ConditionDeclaration,
        context: dict[str, Any],
    ) -> bool: ...
