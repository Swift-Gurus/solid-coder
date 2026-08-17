"""Defines explicit audit evidence for legacy condition events."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


"""
solid-name: UnavailableConditionEvidence
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents unavailable condition audit evidence for legacy events.
"""
class UnavailableConditionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["unavailable"] = "unavailable"
    matched: bool
    reason: str = "legacy event did not persist condition evidence"
