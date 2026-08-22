"""Defines the changed portions of a prospective source revision."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: ChangedContent
solid-category: model
solid-description: Represents the previous and prospective portions selected from a source revision.
solid-tags: [hook]
"""
class ChangedContent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    previous: str
    prospective: str
