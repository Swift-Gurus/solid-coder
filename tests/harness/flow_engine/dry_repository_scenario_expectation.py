"""Defines expected candidate and review results for one DRY repository scenario."""

from pydantic import BaseModel, ConfigDict, Field

from dry_duplication_classification import DRYDuplicationClassification
from dry_reuse_classification import DRYReuseClassification
from findings.review_severity import ReviewSeverity
from rule_metric_result_expectation import RuleMetricResultExpectation


"""
solid-name: DRYRepositoryScenarioExpectation
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries expected reuse, duplication, metric, exception, and severity decisions for one isolated DRY repository scenario.
"""
class DRYRepositoryScenarioExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_name: str = Field(min_length=1)
    reuse_classification: DRYReuseClassification
    duplication_classification: DRYDuplicationClassification
    metrics: list[RuleMetricResultExpectation] = Field(min_length=1)
    is_exception: bool
    severity: ReviewSeverity
