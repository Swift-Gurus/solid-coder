"""Defines categories of deterministic source technology detections."""

from enum import Enum


"""
solid-name: TechnologyDetectionCategory
solid-category: model
solid-spec: [SPEC-040]
solid-description: Enumerates language, framework, capability, and unit-trait source detections.
"""
class TechnologyDetectionCategory(str, Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    UNIT_TRAIT = "unit_trait"
