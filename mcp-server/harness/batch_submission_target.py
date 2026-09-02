"""Identifies one model-facing batch label and its existing engine instance."""

from dataclasses import dataclass


"""
solid-name: BatchSubmissionTarget
solid-category: model
solid-spec: [SPEC-042]
solid-description: Associates one domain label with the existing step instance that owns its output validation and events.
"""
@dataclass(frozen=True)
class BatchSubmissionTarget:
    label: str
    instance_id: str
