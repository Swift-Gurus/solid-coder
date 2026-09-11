"""Identifies one model-facing batch label and its existing engine instance."""

from dataclasses import dataclass
"""
solid-name: BatchSubmissionTarget
solid-category: model
solid-spec: [SPEC-042, SPEC-043, SPEC-045]
solid-description: Associates a model-facing batch address with the existing step instance that owns validation and events.
"""
@dataclass(frozen=True)
class BatchSubmissionTarget:
    label: str
    instance_id: str
    workflow_alias: str = ""
    step_id: str = ""
