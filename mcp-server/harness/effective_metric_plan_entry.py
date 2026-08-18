"""Defines one resolved metric in an effective review-rule plan."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from harness.metric_policy_override_audit import MetricPolicyOverrideAudit
from harness.metric_scoring_declaration import MetricScoringDeclaration


"""
solid-name: EffectiveMetricPlanEntry
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents authored and effective enablement and scoring for one workflow metric.
"""
class EffectiveMetricPlanEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str
    authored_enabled: bool = True
    effective_enabled: bool
    authored_scoring: MetricScoringDeclaration
    effective_scoring: MetricScoringDeclaration
    policy_override: Optional[MetricPolicyOverrideAudit] = None
