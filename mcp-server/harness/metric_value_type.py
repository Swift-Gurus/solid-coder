"""Defines scalar value types supported by executable review metrics."""

from enum import Enum


"""
solid-name: MetricValueType
solid-category: model
solid-spec: [SPEC-039]
solid-description: Enumerates the scalar JSON value types accepted from a metric observation.
"""
class MetricValueType(str, Enum):
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
