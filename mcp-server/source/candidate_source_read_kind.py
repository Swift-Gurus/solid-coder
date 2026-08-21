"""Defines typed outcomes for candidate source loading."""

from enum import Enum


"""
solid-name: CandidateSourceReadKind
solid-category: model
solid-spec: [SPEC-040]
solid-description: Identifies whether candidate source was loaded or why its snapshotted identity could not be honored.
"""
class CandidateSourceReadKind(str, Enum):
    LOADED = "loaded"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    ESCAPED_ROOT = "escaped_root"
    CHANGED = "changed"
