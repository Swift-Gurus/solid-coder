"""Identifies one model-facing batch label and its existing engine instance."""

from dataclasses import dataclass
from typing import Optional


"""
solid-name: BatchSubmissionTarget
solid-category: model
solid-spec: [SPEC-042, SPEC-043]
solid-description: Associates a domain label and optional authored rule alias with the existing step instance that owns validation and events.
"""
@dataclass(frozen=True)
class BatchSubmissionTarget:
    label: str
    instance_id: str
    rule_alias: Optional[str] = None
