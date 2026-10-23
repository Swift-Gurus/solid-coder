"""Language-neutral type-inspection syntax categories."""

from enum import Enum

"""
solid-name: SourceTypeInspectionKind
solid-category: model
solid-spec: [SPEC-063]
solid-description: Distinguishes type-inspection operations without inferring ownership, runtime safety, or review severity.
"""


class SourceTypeInspectionKind(str, Enum):
    CONDITIONAL_CAST = "conditional_cast"
    FORCED_CAST = "forced_cast"
    CONVERSION = "conversion"
    TYPE_TEST = "type_test"
    TYPE_QUERY = "type_query"
    PATTERN_CAST = "pattern_cast"
    PATTERN_TYPE_TEST = "pattern_type_test"
