from pathlib import Path
from unittest import TestCase

from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_symbol_provenance import SourceSymbolProvenance
from source.analysis.provenance.source_type_inspection_provenance import (
    SourceTypeInspectionProvenance,
)
from source.analysis.provenance.type_inspection_context_renderer import (
    TypeInspectionContextRenderer,
)
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.source_line_range import SourceLineRange


class TestTypeInspectionContextRenderer(TestCase):
    def test_presents_verified_facts_without_internal_paths_or_symbol_identity(self):
        provenance = SourceSymbolProvenance(
            resolution=SourceDeclarationSymbol(
                symbol_id="private-symbol",
                declaration_path=Path("/private/project/Source.swift"),
            ),
            project_root=Path("/private/project"),
            ownership="developer",
            declaration_path=Path("/private/project/Source.swift"),
            reason="Resolved declaration.",
        )
        fact = SourceTypeInspectionProvenance(
            inspection=SourceTypeInspection(
                identity="inspection-1",
                kind="conditional_cast",
                expression="value as? Concrete",
                operand="value",
                target_tokens=["Concrete"],
                span=SourceLineRange(start=4, end=4),
                start_offset=40,
                end_offset=58,
            ),
            value=provenance,
            contract=provenance,
            destination=provenance,
            verified=True,
        )
        text = TypeInspectionContextRenderer().render(
            [fact, fact.model_copy(update={"verified": False})]
        )
        self.assertEqual(text.count("inspection-1"), 1)
        self.assertIn("value as? Concrete", text)
        self.assertIn("line 4", text)
        self.assertIn("Contract: developer", text)
        self.assertNotIn("/private/project", text)
        self.assertNotIn("private-symbol", text)

    def test_empty_inventory_has_no_presentation(self):
        self.assertEqual(TypeInspectionContextRenderer().render([]), "")
