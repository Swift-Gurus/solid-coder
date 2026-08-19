"""Detects file-scoped tags from exact Swift imports."""

from harness.json_loading import JsonLoading
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_evidence_resolving import SourceEvidenceResolving
from source.source_unit import SourceUnit
from source.swift_import_tag_registration import SwiftImportTagRegistration
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: SwiftImportTagDetector
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Determines auditable file technology tags from exact Swift imports.
"""
class SwiftImportTagDetector:

    def __init__(
        self,
        json_loader: JsonLoading,
        evidence_resolver: SourceEvidenceResolving,
        registrations: list[SwiftImportTagRegistration],
    ) -> None:
        self._json_loader = json_loader
        self._evidence_resolver = evidence_resolver
        self._registrations = registrations

    def detect(
        self,
        parser_document: str,
        source: ResolvedAnalysisSource,
        units: list[SourceUnit],
    ) -> list[TechnologyDetection]:
        document = self._json_loader.safe_load(parser_document)
        items = document.get("items", []) if isinstance(document, dict) else []
        detections: list[TechnologyDetection] = []
        for item in items:
            if not isinstance(item, dict) or item.get("_kind") != "import_decl":
                continue
            module_path = item.get("module_path")
            if not isinstance(module_path, list):
                continue
            module = ".".join(
                part for part in module_path if isinstance(part, str)
            )
            registration = next(
                (
                    candidate
                    for candidate in self._registrations
                    if candidate.module == module
                ),
                None,
            )
            if registration is None:
                continue
            source_range = item.get("range")
            start_offset = (
                source_range.get("start", 0)
                if isinstance(source_range, dict)
                else 0
            )
            end_offset = (
                source_range.get("end", start_offset)
                if isinstance(source_range, dict)
                else start_offset
            )
            evidence = self._evidence_resolver.resolve(
                fact=f"import {module}",
                source=source.text,
                start_offset=start_offset,
                end_offset=end_offset,
            )
            detections.extend(
                TechnologyDetection(
                    tag=tag,
                    detector_identity="swift-import-tags-v1",
                    scope=TechnologyDetectionScope.FILE,
                    scope_identity=source.identity,
                    evidence=[evidence],
                )
                for tag in registration.tags
            )
        return detections
