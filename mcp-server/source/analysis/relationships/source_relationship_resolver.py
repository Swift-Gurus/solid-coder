from typing import Protocol

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.relationships.source_declaration_reference import (
    SourceDeclarationReference,
)
from source.analysis.relationships.source_declaration_relationship import (
    SourceDeclarationRelationship,
)
from source.analysis.relationships.source_reference_candidate_resolving import (
    SourceReferenceCandidateResolving,
)
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)
from source.analysis.relationships.source_relationship_kind import (
    SourceRelationshipKind,
)
from source.source_analysis import SourceAnalysis
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceRelationshipsResolving
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for resolving bounded declaration relationships from inspected source snapshots while retaining uncertainty.
"""


class SourceRelationshipsResolving(Protocol):
    def resolve(
        self, analyses: list[SourceAnalysis]
    ) -> SourceRelationshipInventory: ...


"""
solid-name: SourceRelationshipResolver
solid-category: service
solid-spec: [SPEC-057]
solid-description: Preserves bounded inheritance and extension links, inspected evidence, and uncertainty across supplied source analyses.
"""


class SourceRelationshipResolver(SourceRelationshipsResolving):
    def __init__(self, references: SourceReferenceCandidateResolving) -> None:
        self._references = references

    def resolve(self, analyses: list[SourceAnalysis]) -> SourceRelationshipInventory:
        if len({analysis.source_identity for analysis in analyses}) != len(analyses):
            raise ValueError(
                "Relationship analysis requires one snapshot per source identity"
            )
        relationships: list[SourceDeclarationRelationship] = []
        for analysis in analyses:
            for unit in analysis.units:
                signature = unit.signature
                if signature.kind != "declaration":
                    continue
                owner = SourceUnitIdentity(
                    source_identity=analysis.source_identity,
                    unit_identity=unit.identity,
                )
                references = [
                    SourceDeclarationReference(
                        owner=owner,
                        kind=SourceRelationshipKind.INHERITED_TYPE,
                        target=target,
                        generic_parameters=signature.generic_parameters,
                        constraints=signature.constraints,
                    )
                    for target in signature.inherited_types
                ]
                if unit.kind is ReviewUnitKind.EXTENSION:
                    references.insert(
                        0,
                        SourceDeclarationReference(
                            owner=owner,
                            kind=SourceRelationshipKind.EXTENSION_TARGET,
                            target=signature.name,
                            generic_parameters=signature.generic_parameters,
                            constraints=signature.constraints,
                        ),
                    )
                relationships.extend(
                    self._references.resolve(reference, analyses)
                    for reference in references
                )
        return SourceRelationshipInventory(
            analyses=analyses, relationships=relationships
        )
