"""Checks repository ownership without turning missing semantic evidence into facts."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from gate.gate_exclusion_checker import ExclusionPatternResolving
from source.analysis.provenance.source_declaration_ownership_resolver import (
    SourceDeclarationOwnershipResolver,
)
from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_locationless_ownership_resolver import (
    SourceLocationlessOwnershipResolver,
)
from source.analysis.provenance.source_sdk_symbol import SourceSDKSymbol
from source.analysis.provenance.source_symbol_ownership import SourceSymbolOwnership
from source.analysis.provenance.source_symbol_ownership_resolver import (
    SourceSymbolOwnershipResolver,
)
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol

"""
solid-name: TestSourceSymbolOwnership
solid-category: unit-test
solid-spec: [SPEC-064]
solid-description: Checks declaration ownership, canonical repository boundaries, exclusions and explicit unresolved symbol evidence.
"""


class TestSourceSymbolOwnership(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory(prefix="symbol-ownership-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.root = self.directory / "project"
        self.root.mkdir()
        self.exclusions = Mock(spec=ExclusionPatternResolving)
        self.exclusions.matched_pattern.return_value = None
        self.resolver = SourceSymbolOwnershipResolver(
            declarations=SourceDeclarationOwnershipResolver(self.exclusions),
            locationless=SourceLocationlessOwnershipResolver(),
        )

    def test_unwritten_repository_declaration_is_owned(self) -> None:
        path = self.root / "Sources" / "Unwritten.swift"
        result = self.resolver.resolve(
            SourceDeclarationSymbol(symbol_id="contract", declaration_path=path),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.DEVELOPER)
        self.assertEqual(result.declaration_path, path)
        self.assertEqual(result.project_root, self.root)
        self.assertFalse(path.exists())

    def test_sibling_with_same_root_prefix_is_external(self) -> None:
        path = self.directory / "project-dependency" / "Contract.swift"
        result = self.resolver.resolve(
            SourceDeclarationSymbol(symbol_id="contract", declaration_path=path),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.EXTERNAL)
        self.exclusions.matched_pattern.assert_not_called()

    def test_symlink_escape_uses_actual_declaration_location(self) -> None:
        external = self.directory / "dependency"
        external.mkdir()
        (self.root / "linked").symlink_to(external, target_is_directory=True)
        result = self.resolver.resolve(
            SourceDeclarationSymbol(
                symbol_id="contract",
                declaration_path=self.root / "linked" / "Contract.swift",
            ),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.EXTERNAL)
        self.assertEqual(result.declaration_path, external / "Contract.swift")

    def test_symlinked_project_root_is_canonicalized(self) -> None:
        alias = self.directory / "project-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        result = self.resolver.resolve(
            SourceDeclarationSymbol(
                symbol_id="contract", declaration_path=alias / "Contract.swift"
            ),
            alias,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.DEVELOPER)
        self.assertEqual(result.project_root, self.root)

    def test_excluded_repository_declaration_is_not_proven_external(self) -> None:
        self.exclusions.matched_pattern.return_value = "Tests/**"
        path = self.root / "Tests" / "Contract.swift"
        result = self.resolver.resolve(
            SourceDeclarationSymbol(symbol_id="contract", declaration_path=path),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.EXCLUDED)
        self.assertIn("excluded", result.reason)
        self.assertEqual(result.matched_exclusion, "Tests/**")
        self.exclusions.matched_pattern.assert_called_once_with(str(path))

    def test_verified_sdk_symbol_does_not_require_a_local_path(self) -> None:
        result = self.resolver.resolve(
            SourceSDKSymbol(
                symbol_id="sdk-contract",
                evidence="Semantic service reports isSystem=true.",
            ),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.EXTERNAL)
        self.assertIsNone(result.declaration_path)
        self.assertIn("isSystem=true", result.reason)
        self.exclusions.matched_pattern.assert_not_called()

    def test_unresolved_lookup_remains_unknown(self) -> None:
        result = self.resolver.resolve(
            SourceUnresolvedSymbol(reason="Value type lookup returned no declaration."),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.UNKNOWN)
        self.assertEqual(result.reason, "Value type lookup returned no declaration.")
        self.exclusions.matched_pattern.assert_not_called()

    def test_ambiguous_lookup_remains_unknown(self) -> None:
        result = self.resolver.resolve(
            SourceUnresolvedSymbol(
                kind="ambiguous",
                reason="Two declarations match; binding is unresolved.",
            ),
            self.root,
        )
        self.assertEqual(result.ownership, SourceSymbolOwnership.UNKNOWN)
        self.assertEqual(result.resolution.kind, "ambiguous")

    def test_relative_declaration_path_is_rejected_at_boundary(self) -> None:
        with self.assertRaises(ValueError):
            SourceDeclarationSymbol(
                symbol_id="contract", declaration_path=Path("Contract.swift")
            )

    def test_relative_project_root_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute"):
            self.resolver.resolve(
                SourceUnresolvedSymbol(reason="No declaration."),
                Path("project"),
            )

    def test_recorded_ownership_does_not_change_when_exclusions_change(self) -> None:
        result = self.resolver.resolve(
            SourceDeclarationSymbol(
                symbol_id="contract", declaration_path=self.root / "Contract.swift"
            ),
            self.root,
        )
        persisted = result.model_dump_json()
        self.exclusions.matched_pattern.return_value = "Tests/**"
        restored = type(result).model_validate_json(persisted)
        self.assertEqual(restored, result)
        self.assertEqual(restored.ownership, SourceSymbolOwnership.DEVELOPER)
        self.assertIsNone(restored.matched_exclusion)
        self.assertEqual(self.exclusions.matched_pattern.call_count, 1)
