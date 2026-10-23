"""Defines one resolved metric in an effective review-rule plan."""

from harness.metric_policy_override_audit import MetricPolicyOverrideAudit
from harness.metric_scoring_declaration import MetricScoringDeclaration
from pydantic import BaseModel, ConfigDict

"""
solid-name: EffectiveMetricPlanEntry
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents authored and effective enablement and scoring for one workflow metric.
"""


class EffectiveMetricPlanEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str
    observation_id: str = "value"
    authored_enabled: bool = True
    effective_enabled: bool
    authored_scoring: MetricScoringDeclaration
    effective_scoring: MetricScoringDeclaration
    policy_override: MetricPolicyOverrideAudit | None = None
