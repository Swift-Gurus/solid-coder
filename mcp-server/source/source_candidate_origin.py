"""Defines the authoritative origin of a source-search candidate."""

from enum import Enum


"""
solid-name: SourceCandidateOrigin
solid-category: model
solid-description: Classifies source-search candidate provenance for deterministic resolution and audit.
"""
class SourceCandidateOrigin(str, Enum):
    PROPOSED = "proposed"
    REPOSITORY = "repository"
