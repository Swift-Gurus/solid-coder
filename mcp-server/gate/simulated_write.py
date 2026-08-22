"""Defines the typed result of prospective write simulation."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: SimulatedWrite
solid-category: model
solid-description: Represents prospective file content and its atomic review context before a write is authorized.
solid-tags: [hook]
"""
class SimulatedWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content: str
    existing_content: str
    low_risk: bool
