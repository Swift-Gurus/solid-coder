from typing import Protocol

from source.analysis.relationships.source_related_declaration import (
    SourceRelatedDeclaration,
)
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)
from source.analysis.relationships.source_relationship_kind import (
    SourceRelationshipKind,
)
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceRelatedDeclarationsSelecting
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for selecting inspected declaration owners linked to one target without interpreting conformance or review policy.
"""


class SourceRelatedDeclarationsSelecting(Protocol):
    def select(
        self, inventory: SourceRelationshipInventory, declaration: SourceUnitIdentity
    ) -> list[SourceRelatedDeclaration]: ...


"""
solid-name: SourceRelatedDeclarationsSelector
solid-category: service
solid-spec: [SPEC-057]
solid-description: Selects declaration owners whose recorded inherited-type links include a target identity, retaining ambiguous and conditional relationships.
"""


class SourceRelatedDeclarationsSelector(SourceRelatedDeclarationsSelecting):
    def select(
        self, inventory: SourceRelationshipInventory, declaration: SourceUnitIdentity
    ) -> list[SourceRelatedDeclaration]:
        return [
            SourceRelatedDeclaration(declaration=unit, relationship=relationship)
            for relationship in inventory.relationships
            if relationship.reference.kind is SourceRelationshipKind.INHERITED_TYPE
            and declaration in relationship.candidates
            for analysis in inventory.analyses
            if analysis.source_identity == relationship.reference.owner.source_identity
            for unit in analysis.units
            if unit.identity == relationship.reference.owner.unit_identity
        ]
