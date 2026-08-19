"""Defines scopes of deterministic source technology detections."""

from enum import Enum


"""
solid-name: TechnologyDetectionScope
solid-category: model
solid-spec: [SPEC-040]
solid-description: Enumerates file-scoped and source-unit-scoped technology evidence.
"""
class TechnologyDetectionScope(str, Enum):
    FILE = "file"
    UNIT = "unit"
