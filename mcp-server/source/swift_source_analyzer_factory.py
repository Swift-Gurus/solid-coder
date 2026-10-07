"""Composes deterministic Swift source analysis."""

from source.analysis.tree_sitter_swift_inventory_parser_factory import (
    TreeSitterSwiftInventoryParserFactory,
)
from source.swift_import_tag_detector import SwiftImportTagDetector
from source.swift_import_tag_registration import SwiftImportTagRegistration
from source.swift_source_analyzer import SwiftSourceAnalyzer
from source.swift_syntax_registration_matcher import (
    SwiftSyntaxRegistrationMatcher,
)
from source.swift_syntax_tag_detector import SwiftSyntaxTagDetector
from source.swift_syntax_tag_registration import SwiftSyntaxTagRegistration
from source.swift_tag_detector import SwiftTagDetector
from source.swift_view_tag_detector import SwiftViewTagDetector


"""
solid-name: SwiftSourceAnalyzerFactory
solid-category: factory
solid-spec: [SPEC-040, SPEC-062]
solid-description: Provides parsed Swift units and members, diagnostics, and auditable built-in technology detections from immutable source.
"""
class SwiftSourceAnalyzerFactory:
    def make(self) -> SwiftSourceAnalyzer:
        return SwiftSourceAnalyzer(
            parser=TreeSitterSwiftInventoryParserFactory().make(),
            tag_detector=SwiftTagDetector([
                SwiftImportTagDetector(
                    registrations=[
                        SwiftImportTagRegistration(
                            module="SwiftUI",
                            tags=["ui", "swiftui"],
                        ),
                        SwiftImportTagRegistration(
                            module="UIKit",
                            tags=["ui", "uikit"],
                        ),
                        SwiftImportTagRegistration(
                            module="ComposableArchitecture",
                            tags=["tca"],
                        ),
                        SwiftImportTagRegistration(
                            module="Dispatch",
                            tags=["concurrency", "gcd"],
                        ),
                    ],
                ),
                SwiftViewTagDetector(),
                SwiftSyntaxTagDetector(
                    matcher=SwiftSyntaxRegistrationMatcher(),
                    registrations=[
                        SwiftSyntaxTagRegistration(
                            signals=[
                                "async",
                                "await",
                                "actor",
                                "Task",
                                "Sendable",
                                "MainActor",
                                "nonisolated",
                            ],
                            tags=["concurrency", "structured-concurrency"],
                        ),
                        SwiftSyntaxTagRegistration(
                            signals=["Testing"],
                            tags=["testing", "unit-test"],
                        ),
                        SwiftSyntaxTagRegistration(
                            signals=["XCTest"],
                            excluded_signals=["XCUIApplication"],
                            tags=["testing", "xctest", "unit-test"],
                        ),
                        SwiftSyntaxTagRegistration(
                            signals=["XCUIApplication"],
                            tags=["testing", "xctest", "ui-test"],
                        ),
                    ],
                ),
            ]),
        )
