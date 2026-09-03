"""Defines identity validation for metrics owned by one rule."""

from typing import Protocol

from harness.metric_declaration import MetricDeclaration


"""
solid-name: RuleMetricIdentityValidating
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-044]
solid-description: Contract for validating metric identities within one executable rule workflow.
"""
class RuleMetricIdentityValidating(Protocol):
    def validate(
        self,
        workflow_id: str,
        metrics: list[MetricDeclaration],
    ) -> None: ...
