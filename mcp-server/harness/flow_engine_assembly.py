"""Defines the assembled services of the flow execution engine."""

from __future__ import annotations

from dataclasses import dataclass
from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.dag_running import DAGRunning
from harness.dynamic_workflow_steps_resolving import DynamicWorkflowStepsResolving
from harness.event_appender import EventAppending
from harness.event_replayer import EventReplayer
from harness.flow_loading import FlowLoading
from harness.interpolator import TemplateRendering
from harness.schema_validator import SchemaValidator


"""
solid-name: FlowEngineAssembly
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Provides workflow loading, runtime materialization, execution, event, interpolation, and validation services.
"""
@dataclass(frozen=True)
class FlowEngineAssembly:
    flow_loader: FlowLoading
    event_appender: EventAppending
    event_replayer: EventReplayer
    dynamic_step_resolver: DynamicWorkflowStepsResolving
    dag_runner: DAGRunning
    condition_evaluator: ConditionDecisionEvaluating
    interpolator: TemplateRendering
    schema_validator: SchemaValidator
