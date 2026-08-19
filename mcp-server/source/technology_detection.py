"""Defines one auditable deterministic source technology detection."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_evidence import SourceEvidence
from source.technology_detection_category import TechnologyDetectionCategory
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: TechnologyDetection
solid-category: model
solid-spec: [SPEC-040]
solid-description: Records a normalized technology tag, detector identity, scope, and non-empty source evidence.
"""
class TechnologyDetection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tag: str = Field(min_length=1)
    category: TechnologyDetectionCategory
    detector_identity: str = Field(min_length=1)
    scope: TechnologyDetectionScope
    scope_identity: str = Field(min_length=1)
    evidence: list[SourceEvidence] = Field(min_length=1)
