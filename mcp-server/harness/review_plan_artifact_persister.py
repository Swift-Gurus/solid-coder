"""Persists effective review planning artifacts before rule execution."""

from pathlib import Path

from harness.effective_rule_plan import EffectiveRulePlan
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: ReviewPlanArtifactPersister
solid-category: service
solid-spec: [SPEC-039]
solid-description: Preserves effective review planning and project-policy snapshots for durable audit.
"""
class ReviewPlanArtifactPersister:
    def persist(
        self,
        run_dir: Path,
        plan: EffectiveRulePlan,
        policy_resolution: ReviewPolicyResolution,
    ) -> None:
        (run_dir / "effective-rule-plan.json").write_text(
            plan.model_dump_json(indent=2),
            encoding="utf-8",
        )
        if policy_resolution.authored_content:
            (run_dir / "review-policy.yaml").write_text(
                policy_resolution.authored_content,
                encoding="utf-8",
            )
