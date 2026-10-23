"""Defines language-neutral direct member kinds."""

from enum import Enum

"""
solid-name: SourceMemberKind
solid-category: model
solid-spec: [SPEC-062]
solid-description: Identifies direct declaration members without conflating lifecycle entry points with methods.
"""


class SourceMemberKind(str, Enum):
    METHOD = "method"
    PROPERTY = "property"
    ASSOCIATED_TYPE = "associated_type"
    INITIALIZER = "initializer"
    DEINITIALIZER = "deinitializer"
    SUBSCRIPT = "subscript"
