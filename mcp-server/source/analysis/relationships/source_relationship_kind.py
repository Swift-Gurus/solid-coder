from enum import Enum


"""
solid-name: SourceRelationshipKind
solid-category: model
solid-spec: [SPEC-057]
solid-description: Identifies authored inheritance references and extension targets without asserting semantic conformance.
"""
class SourceRelationshipKind(str, Enum):
    INHERITED_TYPE = "inherited_type"
    EXTENSION_TARGET = "extension_target"
