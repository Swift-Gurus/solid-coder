"""Defines persistence of effective review planning artifacts."""

from pathlib import Path
from typing import Protocol

from harness.effective_rule_plan import EffectiveRulePlan
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: ReviewPlanArtifactPersisting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for preserving effective review planning and policy snapshots for durable audit.
"""
class ReviewPlanArtifactPersisting(Protocol):
    def persist(
        self,
        run_dir: Path,
        plan: EffectiveRulePlan,
        policy_resolution: ReviewPolicyResolution,
    ) -> None: ...
