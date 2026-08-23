"""Defines the event identity needed by live comparison evidence."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: FlowAuditEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Projects a persisted flow event into the stable identity used for retry and error accounting.
"""
class FlowAuditEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    event: str = Field(min_length=1)
