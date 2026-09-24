"""Applies project review policy after workflow assembly."""

from harness.effective_metric_scoring_applier import (
    EffectiveMetricScoringApplying,
)
from harness.flow_def import FlowDef
from harness.flow_loading import FlowLoading
from harness.review_policy_loading import ReviewPolicyLoading


"""
solid-name: PolicyApplyingFlowLoader
solid-category: boundary-adapter
solid-spec: [SPEC-039, SPEC-053]
solid-description: Loads workflows with resolved project scoring policy applied.
"""
class PolicyApplyingFlowLoader(FlowLoading):
    def __init__(
        self,
        delegate: FlowLoading,
        policy_loader: ReviewPolicyLoading,
        scoring_applier: EffectiveMetricScoringApplying,
    ) -> None:
        self._delegate = delegate
        self._policy_loader = policy_loader
        self._scoring_applier = scoring_applier

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        return self._scoring_applier.apply(
            self._delegate.load(path, search_paths),
            self._policy_loader.load(),
        )
