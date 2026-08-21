"""Defines publication states for included-workflow results."""

from enum import Enum


"""
solid-name: WorkflowPublicationState
solid-category: model
solid-spec: [SPEC-037]
solid-description: Enumerates pending, omitted, and publishable included-workflow results.
"""
class WorkflowPublicationState(str, Enum):
    PENDING = "pending"
    OMITTED = "omitted"
    PUBLISHABLE = "publishable"
