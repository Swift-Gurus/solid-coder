"""Repository ownership and review eligibility are distinct outcomes."""

from enum import Enum

"""
solid-name: SourceSymbolOwnership
solid-category: model
solid-spec: [SPEC-064]
solid-description: Distinguishes project ownership, verified external ownership, excluded declarations and unknown provenance.
"""


class SourceSymbolOwnership(str, Enum):
    DEVELOPER = "developer"
    EXTERNAL = "external"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"
