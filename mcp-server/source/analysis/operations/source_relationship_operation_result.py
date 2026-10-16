from harness.operations.operation_result import OperationResult
from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory


"""
solid-name: SourceRelationshipOperationResult
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries typed relationship-analysis evidence and ordered links for downstream workflow processing.
"""
class SourceRelationshipOperationResult(OperationResult[SourceRelationshipInventory]):
    relationships: list[SourceDeclarationRelationship]
