"""Defines the supported source-code unit kinds in review submissions."""

from enum import Enum


"""
solid-name: ReviewUnitKind
solid-category: model
solid-description: Enumerates the closed set of source-code unit kinds accepted in review submissions.
"""
class ReviewUnitKind(str, Enum):
    CLASS = "class"
    STRUCT = "struct"
    ENUM = "enum"
    PROTOCOL = "protocol"
    EXTENSION = "extension"
    ACTOR = "actor"
    FUNCTION = "function"
