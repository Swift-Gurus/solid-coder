"""Defines the optional audit payload in the append-only run event stream."""

from pydantic import BaseModel, ConfigDict

from harness.aggregate_phase import AggregatePhase
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: AggregatePolicyScope
solid-category: model
solid-spec: [SPEC-067]
solid-description: Preserves effective include policy and authored ownership so explicit overrides and inheritance can be traced without model text.
"""
class AggregatePolicyScope(BaseModel):
    model_config = ConfigDict(frozen=True)

    alias: str
    owner_alias: str | None
    execution: WorkflowExecutionMode
    presentation: WorkflowPresentationMode
    execution_declared: bool
    presentation_declared: bool


"""
solid-name: AggregatePhaseAudit
solid-category: model
solid-spec: [SPEC-067]
solid-description: Preserves a phase frontier and its split reasons without becoming execution or model-facing state.
"""
class AggregatePhaseAudit(BaseModel):
    model_config = ConfigDict(frozen=True)

    turn_count: int
    phases: list[AggregatePhase]
    root_execution: WorkflowExecutionMode
    root_presentation: WorkflowPresentationMode
    policy_scopes: list[AggregatePolicyScope]


"""
solid-name: AggregatePhaseAuditEnvelope
solid-category: model
solid-spec: [SPEC-067]
solid-description: Decodes optional phase diagnostics at the JSONL boundary while ignoring unrelated event fields.
"""
class AggregatePhaseAuditEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    audit: AggregatePhaseAudit | None = None
