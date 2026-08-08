"""Detects circular workflow include traversals."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating


"""
solid-name: IncludeCycleGuard
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Rejects repeated workflow sources and reports the active path or workflow-ID chain.
"""
class IncludeCycleGuard:

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def check(
        self,
        identity: str | None,
        label: str | None,
        ancestor_identities: list[str],
        ancestor_labels: list[str],
    ) -> None:
        if identity is not None and identity in ancestor_identities:
            raise self._error_factory.create(
                f"Circular include detected: {' -> '.join(ancestor_labels + [label or identity])}"
            )
