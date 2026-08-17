"""Defines ownership recorded for an enrolled review workflow."""

from enum import Enum


"""
solid-name: RuleWorkflowOrigin
solid-category: model
solid-spec: [SPEC-039]
solid-description: Classifies ownership provenance for enrolled review workflows.
"""
class RuleWorkflowOrigin(str, Enum):
    PROJECT = "project"
    PLUGIN = "plugin"
