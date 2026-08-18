"""Validates review policy targets against enrolled workflow capabilities."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.review_policy_target_validating import ReviewPolicyTargetValidating
from harness.workflow_catalog import WorkflowCatalog


"""
solid-name: ReviewPolicyTargetValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Rejects project review-policy records that target workflows outside the enrolled review-rule catalog.
"""
class ReviewPolicyTargetValidator(ReviewPolicyTargetValidating):

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(
        self,
        catalog: WorkflowCatalog,
        policy_resolution: ReviewPolicyResolution,
    ) -> None:
        for override in policy_resolution.policy.rules:
            source = catalog.find(override.workflow_id)
            if source is None or source.rule is None:
                raise self._error_factory.create(
                    f"Review policy targets unknown rule workflow '{override.workflow_id}'"
                )
