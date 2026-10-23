"""Defines source-declared member access boundaries."""

from enum import Enum

"""
solid-name: SourceMemberVisibility
solid-category: model
solid-spec: [SPEC-062]
solid-description: Identifies declaration access boundaries used to select source members without model inference.
"""


class SourceMemberVisibility(str, Enum):
    PRIVATE = "private"
    FILEPRIVATE = "fileprivate"
    INTERNAL = "internal"
    PACKAGE = "package"
    PUBLIC = "public"
    OPEN = "open"
