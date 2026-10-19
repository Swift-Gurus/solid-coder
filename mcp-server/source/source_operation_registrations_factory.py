"""Composes logical source-operation registrations."""

from pathlib import Path

from harness.operation_registration import OperationRegistration
from harness.operations.operation_result import OperationResult
from harness.operations.result_operation_adapter import ResultOperationAdapter
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.project_context import ProjectDirectoryReading
from hooks.pathlib_extractor import PathlibExtractor
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer
from source.analysis.operations.source_analysis_operation_registrations_factory import (
    SourceAnalysisOperationRegistrationsFactory,
)
from source.analysis.operations.discover_source_declaration_input import DiscoverSourceDeclarationInput
from source.analysis.operations.source_declaration_discovery import SourceDeclarationDiscovery
from source.analysis.operations.source_declaration_discovery_operation_factory import SourceDeclarationDiscoveryOperationFactory
from source.analysis.provenance.resolve_type_inspections_input import ResolveTypeInspectionsInput
from source.analysis.provenance.resolved_type_inspections import ResolvedTypeInspections
from source.analysis.provenance.source_type_inspection_operation_factory import SourceTypeInspectionOperationFactory
from source.collect_changes_input import CollectChangesInput
from source.collect_changes_operation_factory import CollectChangesOperationFactory
from source.collect_changes_output import CollectChangesOutput
from source.exact_source_tokens_resolver_factory import (
    ExactSourceTokensResolverFactory,
)
from source.prepare_search_query_input import PrepareSearchQueryInput
from source.prepare_search_query_operation import PrepareSearchQueryOperation
from source.prepare_search_query_output import PrepareSearchQueryOutput
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.prepare_search_targets_output import PrepareSearchTargetsOutput
from source.present_source_search_operation import PresentSourceSearchOperation
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_operation_factory import (
    ReadSourceCandidatesOperationFactory,
)
from source.read_source_candidates_output import ReadSourceCandidatesOutput
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_output import SourceSearchOutput
from source.source_search_presentation import SourceSearchPresentation
from source.source_search_results import SourceSearchResults
from source.validate_candidate_selection_input import (
    ValidateCandidateSelectionInput,
)
from source.validate_candidate_selection_operation import (
    ValidateCandidateSelectionOperation,
)
from source.validate_candidate_selection_output import (
    ValidateCandidateSelectionOutput,
)
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidator


"""
solid-name: SourceOperationRegistrationsFactory
solid-category: factory
solid-spec: [SPEC-040, SPEC-057]
solid-description: Composes typed logical operation registrations for deterministic source services.
"""
class SourceOperationRegistrationsFactory:
    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def make(self) -> list[OperationRegistration]:
        return [
            OperationRegistration(
                name="source.collect_changes",
                input_model=CollectChangesInput,
                output_model=CollectChangesOutput,
                handler=CollectChangesOperationFactory().make(),
            ),
            *SourceAnalysisOperationRegistrationsFactory().make(),
            OperationRegistration(
                name="source.resolve_type_inspections",
                input_model=ResolveTypeInspectionsInput,
                output_model=ResolvedTypeInspections,
                handler=SourceTypeInspectionOperationFactory(self._project_directory).make(),
            ),
            OperationRegistration(
                name="source.discover_declaration",
                input_model=DiscoverSourceDeclarationInput,
                output_model=OperationResult[SourceDeclarationDiscovery],
                handler=ResultOperationAdapter(
                    operation=SourceDeclarationDiscoveryOperationFactory(self._project_directory).make(),
                    result_type=OperationResult[SourceDeclarationDiscovery],
                ),
            ),
            OperationRegistration(
                name="source.prepare_search_targets",
                input_model=PrepareSearchTargetsInput,
                output_model=PrepareSearchTargetsOutput,
                handler=PrepareSearchTargetsOperationFactory().make(),
            ),
            OperationRegistration(
                name="source.prepare_search_query",
                input_model=PrepareSearchQueryInput,
                output_model=PrepareSearchQueryOutput,
                handler=PrepareSearchQueryOperation(
                    tokens=ExactSourceTokensResolverFactory().make(),
                    extension=PathlibExtractor(
                        lambda path: Path(path).suffix.lower()
                    ),
                ),
            ),
            OperationRegistration(
                name="source.search",
                input_model=SourceSearchInput,
                output_model=SourceSearchOutput,
                handler=SourceSearchOperationFactory().make(
                    self._project_directory,
                ),
            ),
            OperationRegistration(
                name="source.present_search",
                input_model=SourceSearchResults,
                output_model=SourceSearchPresentation,
                handler=PresentSourceSearchOperation(
                    renderer=CodebaseSearchOutputRenderer(),
                    project_directory=self._project_directory,
                ),
            ),
            OperationRegistration(
                name="source.validate_candidate_selection",
                input_model=ValidateCandidateSelectionInput,
                output_model=ValidateCandidateSelectionOutput,
                handler=ValidateCandidateSelectionOperation(
                    coverage_validator=CollectionIdentityCoverageValidator(FlowValidationErrorFactory()),
                ),
            ),
            OperationRegistration(
                name="source.read_candidates",
                input_model=ReadSourceCandidatesInput,
                output_model=ReadSourceCandidatesOutput,
                handler=ReadSourceCandidatesOperationFactory(
                    self._project_directory
                ).make(),
            ),
        ]
