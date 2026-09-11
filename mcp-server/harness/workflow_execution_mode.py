"""Defines execution modes for workflow aggregation boundaries."""

from enum import Enum


"""
solid-name: WorkflowExecutionMode
solid-category: model
solid-spec: [SPEC-045]
solid-description: Selects granular or aggregate execution within one explicitly owned workflow boundary.
"""
class WorkflowExecutionMode(str, Enum):
    GRANULAR = "granular"
    AGGREGATE = "aggregate"
