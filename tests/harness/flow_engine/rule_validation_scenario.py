"""Defines one typed deterministic rule-workflow validation scenario."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind
from findings.review_severity import ReviewSeverity
from harness.rule_scope import RuleScope
from rule_analysis_expectation import RuleAnalysisExpectation
from rule_metric_expectation import RuleMetricExpectation


"""
solid-name: RuleValidationScenario
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries canonical source, fixture, metric, and final-severity expectations for one executable rule.
"""
class RuleValidationScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str = Field(min_length=1)
    rule_path: Path
    fixture_path: Path
    analysis: list[RuleAnalysisExpectation] = Field(default_factory=list)
    metrics: list[RuleMetricExpectation] = Field(min_length=1)
    final_severity: ReviewSeverity
    rule_scope: RuleScope = RuleScope.UNIT
    included_file_extensions: list[str] = Field(default_factory=list)
    included_unit_kinds: list[ReviewUnitKind] = Field(default_factory=list)
    included_tags: list[str] = Field(default_factory=list)
    has_authored_exceptions: bool = True
