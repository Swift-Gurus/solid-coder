from enum import Enum


"""
solid-name: SourceRelationshipStatus
solid-category: model
solid-spec: [SPEC-057]
solid-description: Distinguishes a bounded relationship candidate from ambiguous or unresolved references without representing semantic verification.
"""
class SourceRelationshipStatus(str, Enum):
    CANDIDATE = "candidate"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"
