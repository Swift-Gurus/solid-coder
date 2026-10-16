from harness.project_context import ProjectDirectoryReading
from source.analysis.operations.candidate_source_analysis_visitor import CandidateSourceAnalysisVisitor
from source.analysis.operations.source_candidate_analysis_operation import SourceCandidateAnalysisOperation
from source.analysis.operations.source_declaration_discovery_operation import SourceDeclarationDiscoveryOperation
from source.analysis.relationships.source_reference_candidate_resolver import SourceReferenceCandidateResolver
from source.analysis.relationships.source_related_declarations_selector import SourceRelatedDeclarationsSelector
from source.analysis.relationships.source_relationship_resolver import SourceRelationshipResolver
from source.read_source_candidates_operation_factory import ReadSourceCandidatesOperationFactory
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_search_operation_factory import SourceSearchOperationFactory


"""
solid-name: SourceDeclarationDiscoveryOperationFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Composes shared repository search, verified source inspection, parsing, and bounded relationship selection for declaration discovery.
"""
class SourceDeclarationDiscoveryOperationFactory:
    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def make(self) -> SourceDeclarationDiscoveryOperation:
        analyzer = SourceAnalysisOperationFactory().make()
        return SourceDeclarationDiscoveryOperation(
            searcher=SourceSearchOperationFactory().make(self._project_directory),
            analyzer=SourceCandidateAnalysisOperation(
                reader=ReadSourceCandidatesOperationFactory(self._project_directory).make(),
                analyzer=analyzer,
                candidate_visitor=CandidateSourceAnalysisVisitor(analyzer),
            ),
            relationships=SourceRelationshipResolver(SourceReferenceCandidateResolver()),
            related_declarations=SourceRelatedDeclarationsSelector(),
        )
