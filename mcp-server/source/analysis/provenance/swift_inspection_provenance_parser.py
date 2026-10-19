"""Resolves independent semantic roles for one Swift type inspection."""

from pathlib import Path

from tree_sitter import Node, Tree

from source.analysis.provenance.source_declaration_ownership_resolver import SourceSymbolOwnershipResolving
from source.analysis.provenance.source_symbol_ownership import SourceSymbolOwnership
from source.analysis.provenance.source_symbol_provenance import SourceSymbolResolution
from source.analysis.provenance.source_type_inspection_provenance import SourceTypeInspectionProvenance
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol
from source.analysis.provenance.sourcekit_document import SemanticSymbolLookingUp
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.analysis.type_inspections.source_type_inspection_kind import SourceTypeInspectionKind


"""
solid-name: SwiftInspectionProvenanceParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Resolves the value, contract and destination evidence of a Swift type inspection.
"""
class SwiftInspectionProvenanceParser(SourceSyntaxParsing[SourceTypeInspection, SourceTypeInspectionProvenance]):
    def __init__(
        self,
        tree: Tree,
        document: SemanticSymbolLookingUp,
        positions: SourceSyntaxParsing[Node, int | None],
        values: SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution],
        contracts: SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution],
        types: SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution],
        ownership: SourceSymbolOwnershipResolving[SourceSymbolResolution],
        project_root: Path,
    ) -> None:
        self._tree = tree
        self._document = document
        self._positions = positions
        self._values = values
        self._contracts = contracts
        self._types = types
        self._ownership = ownership
        self._project_root = project_root

    def parse(self, source: SourceTypeInspection) -> SourceTypeInspectionProvenance:
        value_evidence: SourceSymbolResolution = SourceUnresolvedSymbol(reason="The inspected expression has no supported identifier binding.")
        contract_evidence = value_evidence
        destination_evidence: SourceSymbolResolution = SourceUnresolvedSymbol(reason="This inspection has no supported explicit destination type.")
        if source.operand_range is not None:
            operand = self._tree.root_node.descendant_for_byte_range(source.operand_range.start, source.operand_range.end)
            if operand is not None and operand.type == "simple_identifier":
                symbols = self._document.lookup(source.operand_range.start)
                value_evidence = self._values.parse(symbols)
                contract_evidence = self._contracts.parse(symbols)
        if source.destination_range is not None:
            destination = self._tree.root_node.descendant_for_byte_range(source.destination_range.start, source.destination_range.end)
            position = self._positions.parse(destination) if destination is not None else None
            if position is not None:
                destination_evidence = self._types.parse(self._document.lookup(position))
        value = self._ownership.resolve(value_evidence, self._project_root)
        contract = self._ownership.resolve(contract_evidence, self._project_root)
        destination = self._ownership.resolve(destination_evidence, self._project_root)
        required = [value, contract]
        if source.kind is not SourceTypeInspectionKind.TYPE_QUERY:
            required.append(destination)
        limitations = [fact.reason for fact in required if fact.ownership not in {SourceSymbolOwnership.DEVELOPER, SourceSymbolOwnership.EXTERNAL}]
        return SourceTypeInspectionProvenance(
            inspection=source, value=value, contract=contract, destination=destination,
            verified=not limitations, limitations=limitations,
        )
