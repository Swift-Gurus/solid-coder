"""Defines the allowed model disposition for one presented source candidate."""

from enum import Enum

"""
solid-name: SourceCandidateDispositionKind
solid-category: model
solid-spec: [SPEC-056]
solid-description: Distinguishes candidates selected for source inspection from metadata-level rejections.
"""


class SourceCandidateDispositionKind(str, Enum):
    INSPECT = "INSPECT"
    REJECT = "REJECT"
