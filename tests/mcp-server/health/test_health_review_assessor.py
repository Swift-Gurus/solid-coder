"""Tests fail-closed handling of unavailable review metrics."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import _path_bootstrap

from findings.metric_additional_info import MetricAdditionalInfo
from findings.review_severity import ReviewSeverity
from harness.review_result import ReviewResult
from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_decision import RuleMetricDecision
from harness.rule_review_provenance import RuleReviewProvenance
from harness.rule_review_result import RuleReviewResult
from harness.unavailable_rule_metric import UnavailableRuleMetric
from health_review_assessor import HealthReviewAssessor
from scored_review_violation_selector import ScoredReviewViolationSelector
from source.analysis.operations.source_introduction_evidence import SourceIntroductionEvidence
from source.source_unit_identity import SourceUnitIdentity


def rule_result(identity, instance="review-1", severe=False, exception=None):
    info = MetricAdditionalInfo(reasoning="Coverage cannot be verified.", evidence="Audit-only evidence.")
    return RuleReviewResult(
        workflow_id="isp", rule_instance_id=instance,
        provenance=RuleReviewProvenance(kind="included", scope_identity=instance, source_index=0, source_unit=identity),
        severity=ReviewSeverity.SEVERE if severe else None,
        exception=exception or RuleExceptionDecision(is_exception=False, additional_info=info),
        metrics=[RuleMetricDecision(metric_id="ISP-1", value=10, severity=ReviewSeverity.SEVERE, additional_info=info)] if severe else [],
        unavailable_metrics=[UnavailableRuleMetric(metric_id="ISP-2", observation_id="value", additional_info=info)],
    )


@pytest.mark.parametrize("verified,expected_block", [(False, True), (True, False)])
def test_only_a_verified_new_interface_gets_a_warning(verified, expected_block):
    identity = SourceUnitIdentity(source_identity="/project/Feature.swift", unit_identity="Reading")
    evidence = SourceIntroductionEvidence(
        verified_interfaces=[identity] if verified else [],
        reasoning="Original/proposed source comparison.", evidence="Original and proposed hashes.",
    )
    result = ReviewResult(workflow_id="review", severity=None, rule_results=[rule_result(identity)])

    outcome = HealthReviewAssessor(ScoredReviewViolationSelector()).assess(result, evidence)

    assert outcome.violations == []
    assert len(outcome.unavailable_metrics) == 1
    assert outcome.unavailable_metrics[0].blocks_write is expected_block
    assert outcome.unavailable_metrics[0].provenance.source_unit == identity
    assert outcome.unavailable_metrics[0].metric.additional_info.evidence == "Audit-only evidence."
    assert outcome.introduction_evidence == evidence


@pytest.mark.parametrize("identity", [None, SourceUnitIdentity(source_identity="/other/Feature.swift", unit_identity="Reading")])
def test_missing_or_unrelated_identity_cannot_borrow_new_interface_verification(identity):
    evidence = SourceIntroductionEvidence(
        verified_interfaces=[SourceUnitIdentity(source_identity="/project/Feature.swift", unit_identity="Reading")],
        reasoning="Verified one new interface.", evidence="Authoritative source comparison.",
    )
    result = ReviewResult(workflow_id="review", severity=None, rule_results=[rule_result(identity)])

    outcome = HealthReviewAssessor(ScoredReviewViolationSelector()).assess(result, evidence)

    assert outcome.unavailable_metrics[0].blocks_write is True


def test_existing_and_new_interfaces_have_separate_policy_decisions():
    new = SourceUnitIdentity(source_identity="/project/Feature.swift", unit_identity="Added")
    old = SourceUnitIdentity(source_identity="/project/Feature.swift", unit_identity="Existing")
    evidence = SourceIntroductionEvidence(verified_interfaces=[new], reasoning="Added is new.", evidence="Source hashes.")
    result = ReviewResult(workflow_id="review", severity=None, rule_results=[rule_result(new, "new"), rule_result(old, "old")])

    outcome = HealthReviewAssessor(ScoredReviewViolationSelector()).assess(result, evidence)

    assert [item.blocks_write for item in outcome.unavailable_metrics] == [False, True]
    assert [item.rule_instance_id for item in outcome.unavailable_metrics] == ["new", "old"]


def test_new_interface_warning_does_not_suppress_a_measured_severe_finding():
    identity = SourceUnitIdentity(source_identity="/project/Feature.swift", unit_identity="Added")
    evidence = SourceIntroductionEvidence(verified_interfaces=[identity], reasoning="Added is new.", evidence="Source hashes.")
    result = ReviewResult(workflow_id="review", severity=ReviewSeverity.SEVERE, rule_results=[rule_result(identity, severe=True)])

    outcome = HealthReviewAssessor(ScoredReviewViolationSelector()).assess(result, evidence)

    assert [item.metric_id for item in outcome.violations] == ["ISP-1"]
    assert outcome.unavailable_metrics[0].blocks_write is False


@pytest.mark.parametrize("category", ["marker protocol", "test helper"])
def test_whole_interface_exception_is_retained_and_does_not_require_newness(category):
    exception = RuleExceptionDecision(
        is_exception=True,
        additional_info=MetricAdditionalInfo(reasoning=f"Classified as {category}.", evidence="Inspected interface source."),
    )
    result = ReviewResult(workflow_id="review", severity=None, rule_results=[rule_result(None, exception=exception)])
    introductions = SourceIntroductionEvidence(reasoning="No interface was verified new.", evidence="Existing source.")

    outcome = HealthReviewAssessor(ScoredReviewViolationSelector()).assess(result, introductions)

    assert outcome.violations == []
    assert outcome.unavailable_metrics[0].blocks_write is False
    assert outcome.unavailable_metrics[0].exception == exception
    assert outcome.unavailable_metrics[0].metric.status == "unavailable"
