"""Composes per-document Swift semantic inspection capabilities."""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from tree_sitter import Language, Parser
import tree_sitter_swift

from gate.default_exclusion_checker_factory import ExclusionPolicyCreating
from source.analysis.provenance.file_uri_path_parser import FileUriPathParser
from source.analysis.provenance.semantic_symbol_kind import SemanticSymbolKind
from source.analysis.provenance.source_declaration_ownership_resolver import SourceDeclarationOwnershipResolver
from source.analysis.provenance.source_locationless_ownership_resolver import SourceLocationlessOwnershipResolver
from source.analysis.provenance.source_symbol_ownership_resolver import SourceSymbolOwnershipResolver
from source.analysis.provenance.source_type_inspection_provenance import SourceTypeInspectionProvenance
from source.analysis.provenance.sourcekit_document import SemanticSymbolLookingUp
from source.analysis.provenance.sourcekit_document_factory import SemanticDocumentOpening
from source.analysis.provenance.sourcekit_symbol_resolution_parser import SourceKitSymbolResolutionParser
from source.analysis.provenance.swift_binding_annotation_parser import SwiftBindingAnnotationParser
from source.analysis.provenance.swift_inspection_provenance_parser import SwiftInspectionProvenanceParser
from source.analysis.provenance.swift_type_reference_position_parser import SwiftTypeReferencePositionParser
from source.analysis.provenance.swift_value_contract_parser import SwiftValueContractParser
from source.analysis.provenance.utf8_semantic_offset_resolver import UTF8SemanticOffsetResolver
from source.analysis.tree_sitter_nodes_parser import TreeSitterNodesParser
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing, TreeSitterSyntaxParser
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: SwiftInspectionSessionFactory
solid-category: factory
solid-spec: [SPEC-064]
solid-description: Creates document-scoped Swift inspection resolvers.
"""
class SwiftInspectionSessionFactory(SemanticDocumentOpening[SourceSyntaxParsing[SourceTypeInspection, SourceTypeInspectionProvenance]]):
    def __init__(
        self,
        documents: SemanticDocumentOpening[SemanticSymbolLookingUp],
        exclusions: ExclusionPolicyCreating,
    ) -> None:
        self._documents = documents
        self._exclusions = exclusions

    @contextmanager
    def open(self, snapshot: RepositorySourceSnapshot, project_root: Path) -> Iterator[SourceSyntaxParsing[SourceTypeInspection, SourceTypeInspectionProvenance]]:
        tree = TreeSitterSyntaxParser(Parser(Language(tree_sitter_swift.language()))).parse(snapshot.content)
        paths = FileUriPathParser()
        positions = SwiftTypeReferencePositionParser(TreeSitterNodesParser(frozenset(), frozenset()))
        types = SourceKitSymbolResolutionParser(
            allowed_kinds=frozenset({SemanticSymbolKind.CLASS, SemanticSymbolKind.INTERFACE, SemanticSymbolKind.STRUCT, SemanticSymbolKind.ENUM}),
            paths=paths,
        )
        ownership = SourceSymbolOwnershipResolver(
            declarations=SourceDeclarationOwnershipResolver(self._exclusions.create(project_root)),
            locationless=SourceLocationlessOwnershipResolver(),
        )
        with self._documents.open(snapshot, project_root) as document:
            yield SwiftInspectionProvenanceParser(
                tree=tree, document=document, positions=positions,
                values=SourceKitSymbolResolutionParser(frozenset(), paths),
                contracts=SwiftValueContractParser(
                    source=snapshot, annotations=SwiftBindingAnnotationParser(tree),
                    document=document, paths=paths, offsets=UTF8SemanticOffsetResolver(),
                    positions=positions, types=types,
                ),
                types=types, ownership=ownership, project_root=project_root,
            )
