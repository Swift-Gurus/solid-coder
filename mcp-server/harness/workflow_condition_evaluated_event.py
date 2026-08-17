"""Defines the persisted workflow-level condition event payload."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, StrictBool

from harness.condition_evidence import ConditionEvidence


"""
solid-name: WorkflowConditionEvaluatedEvent
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents persisted eligibility state for one workflow invocation.
"""
class WorkflowConditionEvaluatedEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    condition: object
    matched: StrictBool
    evidence: Optional[ConditionEvidence] = None
