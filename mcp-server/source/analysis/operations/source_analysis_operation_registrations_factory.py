from harness.operation_registration import OperationRegistration
from harness.collection_ratio_input import CollectionRatioInput
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.operations.operation_result import OperationResult
from harness.operations.result_operation_adapter import ResultOperationAdapter
from source.analysis.matching.source_declaration_members import SourceDeclarationMembers
from source.analysis.matching.source_owned_members_resolver import SourceOwnedMembersResolver
from source.analysis.matching.source_requirement_matcher_factory import SourceRequirementMatcherFactory
from source.analysis.matching.source_requirement_matches import SourceRequirementMatches
from source.analysis.matching.swift_member_signature_matcher_factory import SwiftMemberSignatureMatcherFactory
from source.analysis.operations.match_source_requirements_input import MatchSourceRequirementsInput
from source.analysis.operations.resolve_source_relationships_input import ResolveSourceRelationshipsInput
from source.analysis.operations.source_declaration_members_input import SourceDeclarationMembersInput
from source.analysis.operations.source_declaration_members_operation import SourceDeclarationMembersOperation
from source.analysis.operations.source_declaration_context import SourceDeclarationContext
from source.analysis.operations.source_declaration_context_input import SourceDeclarationContextInput
from source.analysis.operations.source_declaration_context_operation import SourceDeclarationContextOperation
from source.analysis.operations.source_declaration_context_renderer import SourceDeclarationContextRenderer
from source.analysis.operations.source_relationship_operation import SourceRelationshipOperation
from source.analysis.operations.source_relationship_operation_result import SourceRelationshipOperationResult
from source.analysis.operations.source_requirement_matching_operation import SourceRequirementMatchingOperation
from source.analysis.relationships.source_reference_candidate_resolver import SourceReferenceCandidateResolver
from source.analysis.relationships.source_relationship_resolver import SourceRelationshipResolver
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis import SourceAnalysis
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.analysis.operations.validate_requirement_coverage_input import ValidateRequirementCoverageInput
from source.analysis.operations.validate_requirement_coverage_operation import ValidateRequirementCoverageOperation
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidator


"""
solid-name: SourceAnalysisOperationRegistrationsFactory
solid-category: service
solid-spec: [SPEC-057]
solid-description: Provides typed workflow operations for source inspection, bounded declaration relationships, member contributions, and requirement implementation candidates.
"""
class SourceAnalysisOperationRegistrationsFactory:
    def make(self) -> list[OperationRegistration]:
        members = SourceDeclarationMembersOperation(
            members=SourceOwnedMembersResolver(),
            signatures=SwiftMemberSignatureMatcherFactory().make(),
        )
        return [
            OperationRegistration(
                name="source.analyze",
                input_model=AnalyzeSourceInput,
                output_model=OperationResult[SourceAnalysis],
                handler=ResultOperationAdapter(
                    operation=SourceAnalysisOperationFactory().make(),
                    result_type=OperationResult[SourceAnalysis],
                ),
            ),
            OperationRegistration(
                name="source.resolve_relationships",
                input_model=ResolveSourceRelationshipsInput,
                output_model=SourceRelationshipOperationResult,
                handler=SourceRelationshipOperation(
                    resolver=SourceRelationshipResolver(references=SourceReferenceCandidateResolver()),
                ),
            ),
            OperationRegistration(
                name="source.match_requirements",
                input_model=MatchSourceRequirementsInput,
                output_model=SourceRequirementMatches,
                handler=SourceRequirementMatchingOperation(matcher=SourceRequirementMatcherFactory().make()),
            ),
            OperationRegistration(
                name="source.validate_requirement_coverage",
                input_model=ValidateRequirementCoverageInput,
                output_model=CollectionRatioInput,
                handler=ValidateRequirementCoverageOperation(
                    coverage_validator=CollectionIdentityCoverageValidator(FlowValidationErrorFactory()),
                ),
            ),
            OperationRegistration(
                name="source.declaration_members",
                input_model=SourceDeclarationMembersInput,
                output_model=SourceDeclarationMembers,
                handler=members,
            ),
            OperationRegistration(
                name="source.declaration_context",
                input_model=SourceDeclarationContextInput,
                output_model=SourceDeclarationContext,
                handler=SourceDeclarationContextOperation(
                    members=members,
                    renderer=SourceDeclarationContextRenderer(),
                ),
            ),
        ]
