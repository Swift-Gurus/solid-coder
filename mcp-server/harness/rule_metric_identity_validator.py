"""Validates metric identities owned by one executable rule."""

from harness.metric_declaration import MetricDeclaration
from harness.rule_metric_identity_validating import RuleMetricIdentityValidating
from harness.unique_string_validating import UniqueStringValidating


"""
solid-name: RuleMetricIdentityValidator
solid-category: service
solid-spec: [SPEC-039, SPEC-044]
solid-description: Produces stable metric-observation coordinates and delegates their uniqueness validation.
"""
class RuleMetricIdentityValidator(RuleMetricIdentityValidating):
    def __init__(self, identity_validator: UniqueStringValidating) -> None:
        self._identity_validator = identity_validator

    def validate(
        self,
        workflow_id: str,
        metrics: list[MetricDeclaration],
    ) -> None:
        self._identity_validator.validate(
            [
                (
                    metric.metric_id
                    if metric.observation_id == "value"
                    else f"{metric.metric_id}.{metric.observation_id}"
                )
                for metric in metrics
            ],
            f"metric_id in rule workflow {workflow_id}",
        )
