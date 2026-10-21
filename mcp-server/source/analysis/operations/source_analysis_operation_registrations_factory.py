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
from source.analysis.operations.source_contract_members_operation import SourceContractMembersOperation
from source.analysis.matching.source_contract_members import SourceContractMembers
from source.analysis.operations.bind_member_classifications_input import BindMemberClassificationsInput
from source.analysis.operations.bind_member_classifications_operation import BindMemberClassificationsOperation
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
from source.text_analysis_source import TextAnalysisSource
from source.analysis.operations.text_source_analysis_adapter import TextSourceAnalysisAdapter
from source.analysis.declarations.select_source_declarations_input import SelectSourceDeclarationsInput
from source.analysis.declarations.select_source_declarations_operation import SelectSourceDeclarationsOperation
from source.analysis.declarations.source_declaration_inventory_renderer import SourceDeclarationInventoryRenderer
from source.analysis.declarations.source_declaration_selection_result import SourceDeclarationSelectionResult
from source.analysis.declarations.bind_declaration_classifications_input import BindDeclarationClassificationsInput
from source.analysis.declarations.bind_declaration_classifications_operation import BindDeclarationClassificationsOperation
from source.analysis.declarations.bound_declaration_classifications import BoundDeclarationClassifications
from source.analysis.relationships.source_implementation_owners_resolver import SourceImplementationOwnersResolver
from source.analysis.relationships.source_related_declarations_selector import SourceRelatedDeclarationsSelector
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
                name="source.contract_members",
                input_model=SourceDeclarationMembersInput,
                output_model=SourceContractMembers,
                handler=SourceContractMembersOperation(SourceRequirementMatcherFactory().make()),
            ),
            OperationRegistration(
                name="source.bind_member_classifications",
                input_model=BindMemberClassificationsInput,
                output_model=BindMemberClassificationsInput,
                handler=BindMemberClassificationsOperation(
                    CollectionIdentityCoverageValidator(FlowValidationErrorFactory()),
                ),
            ),
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
                name="source.analyze_text",
                input_model=TextAnalysisSource,
                output_model=OperationResult[SourceAnalysis],
                handler=ResultOperationAdapter(
                    operation=TextSourceAnalysisAdapter(SourceAnalysisOperationFactory().make()),
                    result_type=OperationResult[SourceAnalysis],
                ),
            ),
            OperationRegistration(
                name="source.select_declarations",
                input_model=SelectSourceDeclarationsInput,
                output_model=SourceDeclarationSelectionResult,
                handler=SelectSourceDeclarationsOperation(SourceDeclarationInventoryRenderer()),
            ),
            OperationRegistration(
                name="source.bind_declaration_classifications",
                input_model=BindDeclarationClassificationsInput,
                output_model=BoundDeclarationClassifications,
                handler=BindDeclarationClassificationsOperation(
                    coverage=CollectionIdentityCoverageValidator(FlowValidationErrorFactory()),
                    relationships=SourceRelationshipResolver(SourceReferenceCandidateResolver()),
                    owners=SourceImplementationOwnersResolver(SourceRelatedDeclarationsSelector()),
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
