"""Defines the assembled services of the flow execution engine."""

from __future__ import annotations

from dataclasses import dataclass
from harness.dag_running import DAGRunning
from harness.event_appender import EventAppending
from harness.event_replayer import EventReplayer
from harness.flow_loading import FlowLoading
from harness.interpolator import TemplateRendering
from harness.schema_validator import SchemaValidator


"""
solid-name: FlowEngineAssembly
solid-category: model
solid-spec: [SPEC-030]
solid-description: Provides the resolved loading, execution, event, interpolation, and validation services of a flow engine.
"""
@dataclass(frozen=True)
class FlowEngineAssembly:
    flow_loader: FlowLoading
    event_appender: EventAppending
    event_replayer: EventReplayer
    dag_runner: DAGRunning
    interpolator: TemplateRendering
    schema_validator: SchemaValidator
