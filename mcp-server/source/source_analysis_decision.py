"""Defines deterministic source-analysis completion decisions."""

from enum import Enum


"""
solid-name: SourceAnalysisDecision
solid-category: model
solid-spec: [SPEC-040]
solid-description: Enumerates parsed, partial, and unsupported source-analysis outcomes.
"""
class SourceAnalysisDecision(str, Enum):
    PARSED = "parsed"
    PARTIAL = "partial"
    WHOLE_FILE_UNSUPPORTED = "whole_file_unsupported"
