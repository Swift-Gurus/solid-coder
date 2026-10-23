"""Defines the supported model-facing submission envelopes."""

from enum import Enum

"""
solid-name: FlowSubmissionFormat
solid-category: model
solid-spec: [SPEC-068]
solid-description: Identifies the nested or flat array addressing contract selected for a workflow run.
"""


class FlowSubmissionFormat(str, Enum):
    NESTED = "nested"
    FLAT_ARRAY = "flat_array"
