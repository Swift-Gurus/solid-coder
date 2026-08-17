"""Defines severities that a deterministic scoring band may produce."""

from enum import Enum


"""
solid-name: ScoringBandSeverity
solid-category: model
solid-spec: [SPEC-012, SPEC-039]
solid-description: Enumerates non-compliant severities assignable by an engine-owned scoring band.
"""
class ScoringBandSeverity(str, Enum):
    MINOR = "minor"
    SEVERE = "severe"
