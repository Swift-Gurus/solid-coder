"""Composes logical source-operation registrations."""

from harness.operation_registration import OperationRegistration
from source.analyze_source_input import AnalyzeSourceInput
from source.collect_changes_input import CollectChangesInput
from source.collect_changes_operation_factory import CollectChangesOperationFactory
from source.collect_changes_output import CollectChangesOutput
from source.source_analysis import SourceAnalysis
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory


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
        ]
