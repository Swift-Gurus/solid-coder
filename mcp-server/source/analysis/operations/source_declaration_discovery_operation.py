from harness.operation_handling import OperationHandling
from source.analysis.operations.discover_source_declaration_input import DiscoverSourceDeclarationInput
from source.analysis.operations.source_candidate_analyses import SourceCandidateAnalyses
from source.analysis.operations.source_declaration_discovery import SourceDeclarationDiscovery
from source.analysis.relationships.source_related_declarations_selector import SourceRelatedDeclarationsSelecting
from source.analysis.relationships.source_relationship_resolver import SourceRelationshipsResolving
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.analysis.relationships.source_relationship_kind import SourceRelationshipKind
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.source_analysis import SourceAnalysis
from source.source_search_context import SourceSearchContext
from source.source_search_input import SourceSearchInput
from source.source_search_output import SourceSearchOutput
from source.source_search_query import SourceSearchQuery
from source.source_unit_identity import SourceUnitIdentity
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: SourceDeclarationDiscoveryOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Coordinates bounded name-based discovery of a prepared declaration and its related owners, preserving inspected snapshots and uncertainty for source workflows.
"""
class SourceDeclarationDiscoveryOperation(OperationHandling[DiscoverSourceDeclarationInput, SourceDeclarationDiscovery]):
    def __init__(
        self,
        searcher: OperationHandling[SourceSearchInput, SourceSearchOutput],
        analyzer: OperationHandling[ReadSourceCandidatesInput, SourceCandidateAnalyses],
        relationships: SourceRelationshipsResolving,
        related_declarations: SourceRelatedDeclarationsSelecting,
    ) -> None:
        self._searcher = searcher
        self._analyzer = analyzer
        self._relationships = relationships
        self._related_declarations = related_declarations

    def execute(self, operation_input: DiscoverSourceDeclarationInput) -> SourceDeclarationDiscovery:
        declaration = SourceUnitIdentity(
            source_identity=operation_input.target.source_identity,
            unit_identity=operation_input.target.unit_identity,
        )
        pending = [SourceSearchQuery(id=operation_input.target.identity, terms=[operation_input.target.name])]
        queries: list[SourceSearchQuery] = []
        searches: list[SourceSearchOutput] = []
        analyses: list[SourceAnalysis] = []
        sources: list[TextAnalysisSource] = []
        limitations: list[str] = []
        known_paths = {snapshot.path for snapshot in operation_input.context.sources}
        known_names = {operation_input.target.name}
        for pass_index in range(2 if (
            operation_input.follow_related_declarations or operation_input.follow_inherited_declarations
        ) else 1):
            if not pending:
                break
            queries.extend(pending)
            found = self._searcher.execute(SourceSearchInput(
                queries=pending,
                context=operation_input.context,
                max_candidates=operation_input.max_candidates,
            ))
            searches.append(found)
            if len(found.candidates) == operation_input.max_candidates:
                limitations.append("The candidate limit was reached; discovery completeness is not established.")
            candidates = [candidate for candidate in found.candidates if candidate.path not in known_paths]
            inspected = self._analyzer.execute(ReadSourceCandidatesInput(
                candidates=candidates,
                context=operation_input.context if pass_index == 0 else SourceSearchContext(),
                max_bytes_per_candidate=operation_input.max_bytes_per_candidate,
            ))
            analyses.extend(inspected.analyses)
            sources.extend(inspected.sources)
            limitations.extend(inspected.limitations)
            known_paths.update(candidate.path for candidate in candidates)
            inventory = self._relationships.resolve(analyses)
            related = (
                self._related_declarations.select(inventory, declaration)
                if operation_input.follow_related_declarations else []
            )
            pending = []
            for item in related:
                if item.declaration.name not in known_names:
                    pending.append(SourceSearchQuery(id=item.declaration.identity, terms=[item.declaration.name]))
                    known_names.add(item.declaration.name)
            if operation_input.follow_inherited_declarations:
                owners = [declaration, *[
                    link.reference.owner for link in inventory.relationships
                    if link.reference.kind is SourceRelationshipKind.EXTENSION_TARGET
                    and declaration in link.candidates
                ]]
                for link in inventory.relationships:
                    if link.reference.owner not in owners or link.reference.kind is not SourceRelationshipKind.INHERITED_TYPE:
                        continue
                    name = "".join(link.reference.target.tokens)
                    if name not in known_names:
                        pending.append(SourceSearchQuery(id=name, terms=[name]))
                        known_names.add(name)
        limitations.extend(
            item.relationship.reason for item in related
            if item.relationship.status is not SourceRelationshipStatus.CANDIDATE
        )
        return SourceDeclarationDiscovery(
            inventory=inventory,
            sources=sources,
            declaration=declaration,
            related_declarations=related,
            limitations=limitations,
            queries=queries,
            searches=searches,
        )
