from harness.flow_validation_error import FlowValidationError
from harness.operation_handling import OperationHandling
from findings.review_unit_kind import ReviewUnitKind
from source.source_unit_identity import SourceUnitIdentity
from source.analysis.declarations.associated_declaration_classification import AssociatedDeclarationClassification
from source.analysis.declarations.bind_declaration_classifications_input import BindDeclarationClassificationsInput
from source.analysis.declarations.bound_declaration_classification import BoundDeclarationClassification
from source.analysis.declarations.bound_declaration_classifications import BoundDeclarationClassifications
from source.analysis.declarations.independent_declaration_classification import IndependentDeclarationClassification
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.relationships.source_implementation_owners_resolver import SourceImplementationOwnersResolving
from source.analysis.relationships.source_relationship_resolver import SourceRelationshipsResolving
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidating


"""
solid-name: BindDeclarationClassificationsOperation
solid-category: service
solid-spec: [SPEC-066]
solid-description: Validates complete classification identity coverage and binds evidenced judgments to authoritative declaration and bounded implementation facts for workflow-owned scoring.
"""
class BindDeclarationClassificationsOperation(OperationHandling[BindDeclarationClassificationsInput, BoundDeclarationClassifications]):
    def __init__(self, coverage: CollectionIdentityCoverageValidating,
                 relationships: SourceRelationshipsResolving,
                 owners: SourceImplementationOwnersResolving) -> None:
        self._coverage = coverage
        self._relationships = relationships
        self._owners = owners

    def execute(self, operation_input: BindDeclarationClassificationsInput) -> BoundDeclarationClassifications:
        declarations = operation_input.declarations
        classifications = operation_input.classifications
        self._coverage.validate(
            [entry.identity for entry in declarations],
            [entry.declaration_id for entry in classifications],
            "declaration",
        )
        if any(entry not in operation_input.analysis.declarations for entry in declarations):
            raise FlowValidationError("Selected declarations do not match the authoritative source analysis.")
        inventory = self._relationships.resolve([operation_input.analysis])
        bound: list[BoundDeclarationClassification] = []
        for declaration in declarations:
            classification = next(entry for entry in classifications if entry.declaration_id == declaration.identity)
            related = declaration
            if isinstance(classification, AssociatedDeclarationClassification):
                if declaration.scope_kind is not SourceScopeKind.FILE or declaration.unit.kind is ReviewUnitKind.FUNCTION:
                    raise FlowValidationError(
                        f"Declaration {declaration.identity} must use independent classification. "
                        "Resubmit the complete classifications collection."
                    )
                related = next((entry for entry in declarations
                                if entry.identity == classification.related_declaration_id), None)
                if (related is None or related.identity == declaration.identity
                        or related.scope_kind is not SourceScopeKind.FILE
                        or related.unit.kind is ReviewUnitKind.FUNCTION):
                    raise FlowValidationError(
                        f"Invalid related declaration {classification.related_declaration_id}. "
                        "Choose another displayed file-level type and resubmit the complete classifications collection."
                    )
                if classification.kind == "implemented_contract" and (
                    declaration.unit.kind not in {ReviewUnitKind.PROTOCOL, ReviewUnitKind.CLASS}
                    or related.unit.kind not in {
                        ReviewUnitKind.CLASS, ReviewUnitKind.STRUCT, ReviewUnitKind.ENUM, ReviewUnitKind.ACTOR,
                    }
                ):
                    raise FlowValidationError(
                        f"Invalid implemented_contract relationship from {declaration.unit.name} "
                        f"({declaration.unit.kind.value}) to {related.unit.name} ({related.unit.kind.value}). "
                        "Relate the protocol or base-class contract to its concrete implementation, "
                        "not the implementation to its contract. Resubmit a complete replacement classifications collection."
                    )
                if classification.kind == "cohesive_contract" and (
                    declaration.unit.kind is not ReviewUnitKind.PROTOCOL
                    or related.unit.kind is not ReviewUnitKind.PROTOCOL
                ):
                    raise FlowValidationError(
                        f"Invalid cohesive_contract relationship from {declaration.unit.name} "
                        f"to {related.unit.name}: both declarations must be protocols. "
                        "Use implemented_contract from a contract to its concrete implementation, "
                        "or independent for separate declarations. Resubmit a complete replacement classifications collection."
                    )
                related_classification = next(entry for entry in classifications if entry.declaration_id == related.identity)
                if not isinstance(related_classification, IndependentDeclarationClassification):
                    raise FlowValidationError(
                        f"Related declaration {related.identity} must be independent; association chains and cycles are invalid. "
                        "Resubmit the complete classifications collection."
                    )
            identity = SourceUnitIdentity(source_identity=operation_input.analysis.source_identity,
                                          unit_identity=declaration.unit.identity)
            related_identity = SourceUnitIdentity(source_identity=operation_input.analysis.source_identity,
                                                  unit_identity=related.unit.identity)
            owners = self._owners.resolve(inventory, identity)
            bound.append(BoundDeclarationClassification(
                declaration=declaration,
                kind=classification.kind,
                has_business_logic=(classification.has_business_logic
                                    if isinstance(classification, IndependentDeclarationClassification) else False),
                related_declaration=related,
                declared_implementation=related_identity in owners,
                has_declared_implementation=bool(owners),
                related_has_declared_implementation=bool(self._owners.resolve(inventory, related_identity)),
                additional_info=classification.additional_info,
            ))
        return BoundDeclarationClassifications(declarations=bound)
