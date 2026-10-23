from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_review_provenance import RuleReviewProvenance
from harness.unavailable_rule_metric import UnavailableRuleMetric
from pydantic import BaseModel, ConfigDict

"""
solid-name: UnavailableHealthMetric
solid-category: model
solid-spec: [SPEC-057]
solid-description: Associates an unavailable metric with its reviewed unit and deterministic write-gate decision without inventing severity.
"""


class UnavailableHealthMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str
    rule_instance_id: str
    provenance: RuleReviewProvenance
    metric: UnavailableRuleMetric
    exception: RuleExceptionDecision
    blocks_write: bool
