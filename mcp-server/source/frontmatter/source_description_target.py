"""Compact source identity and authored description for model judgment."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: SourceDescriptionTarget
solid-category: model
solid-spec: [SPEC-069]
solid-description: Identifies the declaration and authored description requiring capability classification without retransmitting source code.
"""
class SourceDescriptionTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration_id: str
    name: str
    label: str
    category: str
    description: str
