"""Rewrites typed rule steps into their public workflow YAML fields."""

from harness.step_def import StepDef
from harness.step_snapshot_rewriting import StepSnapshotRewriting


"""
solid-name: RuleStepSnapshotRewriter
solid-category: boundary
solid-spec: [SPEC-039]
solid-description: Normalizes rule-step snapshots for their public workflow representation.
"""
class RuleStepSnapshotRewriter(StepSnapshotRewriting):
    def rewrite(self, snapshot: dict, step: StepDef) -> None:
        snapshot.pop("metric", None)
        if step.type not in {"metric", "exception"}:
            return
        snapshot.pop("outputs", None)
        if step.metric is None:
            return
        snapshot["metric_id"] = step.metric.metric_id
        if step.metric.observation_id != "value":
            snapshot["observation_id"] = step.metric.observation_id
        snapshot["value"] = step.metric.value.model_dump(
            mode="json",
            exclude_none=True,
        )
        snapshot["scoring"] = step.metric.scoring.model_dump(
            mode="json",
            exclude_none=True,
        )
