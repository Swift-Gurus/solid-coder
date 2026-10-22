"""Carries the cleanup-relevant portion of a host stop event."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: PipelineCleanupEvent
solid-category: model
solid-description: Identifies the optional session transcript associated with a cleanup hook event.
"""
class PipelineCleanupEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    transcript_path: str | None = None
