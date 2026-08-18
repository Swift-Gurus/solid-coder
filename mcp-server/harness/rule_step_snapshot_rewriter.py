"""Rewrites typed rule steps into their public workflow YAML fields."""

from harness.rule_step_snapshot_rewriting import RuleStepSnapshotRewriting
from harness.step_def import StepDef


"""
solid-name: RuleStepSnapshotRewriter
solid-category: boundary
solid-spec: [SPEC-039]
solid-description: Serializes internal metric data into public YAML fields and removes engine-generated rule outputs.
"""
class RuleStepSnapshotRewriter(RuleStepSnapshotRewriting):
    def rewrite(self, snapshot: dict, step: StepDef) -> None:
        snapshot.pop("metric", None)
        if step.type not in {"metric", "exception"}:
            return
        snapshot.pop("outputs", None)
        if step.metric is None:
            return
        snapshot["metric_id"] = step.metric.metric_id
        snapshot["value"] = step.metric.value.model_dump(
            mode="json",
            exclude_none=True,
        )
        snapshot["scoring"] = step.metric.scoring.model_dump(
            mode="json",
            exclude_none=True,
        )
