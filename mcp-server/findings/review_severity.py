"""Defines server-authoritative review severity levels."""

from enum import Enum


"""
solid-name: ReviewSeverity
solid-category: model
solid-description: Enumerates the closed set of server-authoritative review severity levels.
"""
class ReviewSeverity(str, Enum):
    COMPLIANT = "COMPLIANT"
    MINOR = "MINOR"
    SEVERE = "SEVERE"
