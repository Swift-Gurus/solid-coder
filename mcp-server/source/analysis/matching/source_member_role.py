from enum import Enum

"""
solid-name: SourceMemberRole
solid-category: model
solid-spec: [SPEC-057]
solid-description: Identifies whether a member is directly declared, implements an existing declaration, adds behavior, or has unresolved structural identity.
"""


class SourceMemberRole(str, Enum):
    DECLARED = "declared"
    IMPLEMENTATION = "implementation"
    ADDITIONAL = "additional"
    UNRESOLVED = "unresolved"
