"""Defines one aggregate model-execution phase."""

from dataclasses import dataclass, field
from enum import Enum

from harness.step_instance import StepInstance


"""
solid-name: AggregateDeferralReason
solid-category: model
solid-spec: [SPEC-067]
solid-description: Identifies the actual planning or materialization boundary keeping work out of an aggregate phase.
"""
class AggregateDeferralReason(str, Enum):
    WORKFLOW_BOUNDARY = "workflow_boundary"
    EXECUTION_POLICY = "execution_policy"
    ENGINE_OWNED_STEP = "engine_owned_step"
    UNAVAILABLE_CONDITION = "unavailable_condition"
    UNAVAILABLE_COLLECTION = "unavailable_collection"
    PENDING_VALIDATION = "pending_validation"
    UNAVAILABLE_RENDER_INPUT = "unavailable_render_input"


"""
solid-name: AggregatePhaseDeferral
solid-category: model
solid-spec: [SPEC-067]
solid-description: Records a deferred original step, its effective scope, and the unresolved dependencies or binding error.
"""
@dataclass(frozen=True)
class AggregatePhaseDeferral:
    step_id: str
    boundary_id: str
    reason: AggregateDeferralReason
    blocking_step_ids: list[str] = field(default_factory=list)
    detail: str = ""


"""
solid-name: AggregatePhase
solid-category: model
solid-spec: [SPEC-045]
solid-description: Identifies an ordered set of original model-owned steps compiled within one workflow boundary.
"""
@dataclass(frozen=True)
class AggregatePhase:
    boundary_id: str
    step_ids: list[str] = field(default_factory=list)
    instance_ids: list[str] = field(default_factory=list)
    deferrals: list[AggregatePhaseDeferral] = field(default_factory=list)


"""
solid-name: AggregateExpansion
solid-category: model
solid-spec: [SPEC-067]
solid-description: Keeps executable instances separate from internal phase-planning audit evidence.
"""
@dataclass(frozen=True)
class AggregateExpansion:
    ready: list[StepInstance] = field(default_factory=list)
    phases: list[AggregatePhase] = field(default_factory=list)
