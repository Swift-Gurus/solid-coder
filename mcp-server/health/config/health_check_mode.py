"""Identifies the implementation selected for prospective source reviews."""

from enum import Enum


"""
solid-name: HealthCheckMode
solid-category: model
solid-spec: [SPEC-050]
solid-description: Identifies the configured source-health review implementation.
"""
class HealthCheckMode(str, Enum):
    LEGACY = "legacy"
    WORKFLOW = "workflow"
