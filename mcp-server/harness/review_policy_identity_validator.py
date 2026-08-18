"""Validates identity uniqueness throughout a typed client review policy."""

from harness.review_policy import ReviewPolicy
from harness.review_policy_validating import ReviewPolicyValidating
from harness.unique_string_validating import UniqueStringValidating


"""
solid-name: ReviewPolicyIdentityValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Traverses review policy scopes and delegates rule and metric identity checks.
"""
class ReviewPolicyIdentityValidator(ReviewPolicyValidating):

    def __init__(self, identity_validator: UniqueStringValidating) -> None:
        self._identity_validator = identity_validator

    def validate(self, policy: ReviewPolicy) -> None:
        self._identity_validator.validate(
            [rule.workflow_id for rule in policy.rules],
            "review policy workflow_id",
        )
        for rule in policy.rules:
            self._identity_validator.validate(
                [metric.id for metric in rule.metrics],
                "review policy metric ID",
            )
