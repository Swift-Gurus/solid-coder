"""Tests unavailable evidence through the real health gate and decision capture."""

from unittest.mock import Mock

import pytest

from test_health_review_assessor import rule_result
from decision_gate_factory import DecisionGateFactory
from findings.metric_additional_info import MetricAdditionalInfo
from findings.review_severity import ReviewSeverity
from harness.review_result import ReviewResult
from harness.rule_exception_decision import RuleExceptionDecision
from health_outcome_renderer import HealthOutcomeRenderer
from health_review_assessor import HealthReviewAssessor
from health_violation_block_formatter import HealthViolationBlockFormatter
from hook_decision_aggregator import HookDecisionAggregator
from legacy_health_outcome_adapter import LegacyHealthOutcomeAdapter
from safe_health_checker import SafeHealthChecker
from scored_review_violation_selector import ScoredReviewViolationSelector
from source.analysis.operations.source_introduction_evidence import SourceIntroductionEvidence
from source.source_unit_identity import SourceUnitIdentity
from unavailable_health_metric_renderer import UnavailableHealthMetricRenderer


def assessed_outcome(verified=False, excepted=False, severe=False, path="/project/Feature.swift"):
    identity = SourceUnitIdentity(source_identity=path, unit_identity="Reading")
    exception = RuleExceptionDecision(
        is_exception=excepted,
        additional_info=MetricAdditionalInfo(reasoning="Classified interface role.", evidence="Private audit details."),
    )
    result = ReviewResult(
        workflow_id="review", severity=ReviewSeverity.SEVERE if severe else None,
        rule_results=[rule_result(identity, severe=severe, exception=exception)],
    )
    return HealthReviewAssessor(ScoredReviewViolationSelector()).assess(result, SourceIntroductionEvidence(
        verified_interfaces=[identity] if verified else [],
        reasoning="Original/proposed source comparison.", evidence="Original and proposed hashes.",
    ))


def run_gate(outcome, checker=None):
    if checker is None:
        checker = Mock()
        checker.check.return_value = outcome
    gate = DecisionGateFactory().create(Mock())
    allowed = SafeHealthChecker(
        checker=checker,
        renderer=HealthOutcomeRenderer(HealthViolationBlockFormatter(), UnavailableHealthMetricRenderer()),
    ).check("protocol Reading {}", "/project/Feature.swift", "Swift", "parent", gate, "Feature.swift")
    if allowed:
        gate.allow()
    assert allowed is gate.decision.allow
    return gate


@pytest.mark.parametrize("verified,excepted,severe,allowed,warns", [
    (False, False, False, False, False),
    (True, False, False, True, True),
    (False, True, False, True, False),
    (True, False, True, False, True),
])
def test_unavailable_policy_is_enforced_without_fabricated_severity(verified, excepted, severe, allowed, warns):
    gate = run_gate(assessed_outcome(verified, excepted, severe))

    assert gate.decision.allow is allowed
    assert bool(gate.decision.additional_context) is warns
    message = (gate.decision.reason or "") + (gate.decision.additional_context or "")
    assert "Audit-only evidence" not in message
    assert "Private audit details" not in message
    assert ("SEVERE" in message) is severe
    if warns:
        assert "not compliant" in message
    if not allowed and not severe:
        assert "unable to verify" in message.lower()
        assert "retry the same write" in message
        assert "Reading" in message


@pytest.mark.parametrize("legacy_result,allowed", [([], True), (None, False)])
def test_legacy_adapter_preserves_empty_success_and_rejects_absent_results(legacy_result, allowed):
    legacy = Mock()
    legacy.check.return_value = legacy_result
    gate = run_gate(None, checker=LegacyHealthOutcomeAdapter(legacy))
    assert gate.decision.allow is allowed
    assert gate.decision.additional_context is None
    if not allowed:
        assert "Health checker returned no result" in gate.decision.reason


def test_patch_aggregation_retains_new_interface_warning_and_existing_interface_denial():
    new = run_gate(assessed_outcome(verified=True, path="/project/New.swift"))
    existing = run_gate(assessed_outcome(path="/project/Existing.swift"))

    decision = HookDecisionAggregator().aggregate([new.decision, existing.decision])

    assert not decision.allow
    assert "unable to verify" in decision.reason.lower()
    assert "not compliant" in decision.additional_context
    assert existing.decision.additional_context is None
