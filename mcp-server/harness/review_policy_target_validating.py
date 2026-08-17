"""Defines validation of review policy targets against an enrolled catalog."""

from typing import Protocol

from harness.review_policy_resolution import ReviewPolicyResolution
from harness.workflow_catalog import WorkflowCatalog


"""
solid-name: ReviewPolicyTargetValidating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for validating project review-policy targets against enrolled workflow capabilities.
"""
class ReviewPolicyTargetValidating(Protocol):
    def validate(
        self,
        catalog: WorkflowCatalog,
        policy_resolution: ReviewPolicyResolution,
    ) -> None: ...
