"""
solid-name: StepHandlerResolver
solid-category: service
solid-spec: [SPEC-027]
solid-description: Resolves the handler implementation for a given step type.
"""

from __future__ import annotations

from harness.step_handler_resolving import StepHandlerResolving
from harness.step_handling import StepHandling


class StepHandlerResolver(StepHandlerResolving):

    def __init__(self, handlers: dict[str, StepHandling]) -> None:
        self._handlers = handlers

    def resolve(self, step_type: str) -> StepHandling:
        handler = self._handlers.get(step_type)
        if handler is None:
            raise ValueError(f"No step handler registered for type '{step_type}'")
        return handler
