"""Composes logical source-operation registrations."""

from harness.operation_registration import OperationRegistration
from source.analyze_source_input import AnalyzeSourceInput
from source.collect_changes_input import CollectChangesInput
from source.collect_changes_operation_factory import CollectChangesOperationFactory
from source.collect_changes_output import CollectChangesOutput
from source.prepare_search_query_input import PrepareSearchQueryInput
from source.prepare_search_query_operation import PrepareSearchQueryOperation
from source.prepare_search_query_output import PrepareSearchQueryOutput
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.prepare_search_targets_output import PrepareSearchTargetsOutput
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_operation_factory import (
    ReadSourceCandidatesOperationFactory,
)
from source.read_source_candidates_output import ReadSourceCandidatesOutput
from source.source_analysis import SourceAnalysis
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_output import SourceSearchOutput


"""
solid-name: SourceOperationRegistrationsFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Composes typed logical operation registrations for deterministic source services.
"""
class SourceOperationRegistrationsFactory:
    def make(self) -> list[OperationRegistration]:
        return [
            OperationRegistration(
                name="source.collect_changes",
                input_model=CollectChangesInput,
                output_model=CollectChangesOutput,
                handler=CollectChangesOperationFactory().make(),
            ),
            OperationRegistration(
                name="source.analyze",
                input_model=AnalyzeSourceInput,
                output_model=SourceAnalysis,
                handler=SourceAnalysisOperationFactory().make(),
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
                handler=PrepareSearchQueryOperation(),
            ),
            OperationRegistration(
                name="source.search",
                input_model=SourceSearchInput,
                output_model=SourceSearchOutput,
                handler=SourceSearchOperationFactory().make(),
            ),
            OperationRegistration(
                name="source.read_candidates",
                input_model=ReadSourceCandidatesInput,
                output_model=ReadSourceCandidatesOutput,
                handler=ReadSourceCandidatesOperationFactory().make(),
            ),
        ]
