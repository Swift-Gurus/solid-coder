from pydantic import BaseModel, ConfigDict, Field

from health_violation import HealthViolation
from source.analysis.operations.source_introduction_evidence import SourceIntroductionEvidence
from unavailable_health_metric import UnavailableHealthMetric


"""
solid-name: HealthCheckOutcome
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves measured violations, unavailable-metric gate decisions, and their verification evidence as distinct health outcomes.
"""
class HealthCheckOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    violations: list[HealthViolation] = Field(default_factory=list)
    unavailable_metrics: list[UnavailableHealthMetric] = Field(default_factory=list)
    introduction_evidence: SourceIntroductionEvidence | None = None
