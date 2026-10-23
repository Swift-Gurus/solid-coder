from harness.operation_handling import OperationHandling
from source.analysis.operations.resolve_source_relationships_input import (
    ResolveSourceRelationshipsInput,
)
from source.analysis.operations.source_relationship_operation_result import (
    SourceRelationshipOperationResult,
)
from source.analysis.relationships.source_relationship_resolver import (
    SourceRelationshipsResolving,
)

"""
solid-name: SourceRelationshipOperation
solid-category: adapter
solid-spec: [SPEC-057]
solid-description: Exposes bounded declaration relationship analysis as a typed engine-owned operation without performing source discovery or inspection.
"""


class SourceRelationshipOperation(
    OperationHandling[
        ResolveSourceRelationshipsInput, SourceRelationshipOperationResult
    ]
):
    def __init__(self, resolver: SourceRelationshipsResolving) -> None:
        self._resolver = resolver

    def execute(
        self, operation_input: ResolveSourceRelationshipsInput
    ) -> SourceRelationshipOperationResult:
        inventory = self._resolver.resolve(operation_input.analyses)
        return SourceRelationshipOperationResult(
            result=inventory, relationships=inventory.relationships
        )
