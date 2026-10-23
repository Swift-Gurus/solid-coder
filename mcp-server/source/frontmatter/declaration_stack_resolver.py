"""Resolves declaration-scoped stack evidence from registered parser facts."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.frontmatter.stack_registration import StackRegistration
from source.source_analysis import SourceAnalysis
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope

"""
solid-name: DeclarationStackResolver
solid-category: service
solid-spec: [SPEC-069]
solid-description: Matches registered technology usage within individual declarations without promoting file imports to declaration dependencies.
"""


class DeclarationStackResolver(
    SourceSyntaxParsing[SourceAnalysis, list[TechnologyDetection]]
):
    def __init__(self, registrations: list[StackRegistration]) -> None:
        self._registrations = registrations

    def parse(self, source: SourceAnalysis) -> list[TechnologyDetection]:
        imports = {entry.fact for entry in source.imports}
        detections: list[TechnologyDetection] = []
        for declaration in source.declarations:
            for registration in self._registrations:
                if source.file_extension not in registration.file_extensions:
                    continue
                if registration.modules and not imports.intersection(
                    registration.modules
                ):
                    continue
                evidence = [
                    signal
                    for signal in declaration.signals
                    if signal.fact in registration.signals
                ]
                if evidence:
                    detections.append(
                        TechnologyDetection(
                            tag=registration.tag,
                            detector_identity="declaration-stack-syntax-v1",
                            scope=TechnologyDetectionScope.UNIT,
                            scope_identity=declaration.unit.identity,
                            evidence=evidence,
                        )
                    )
        return detections
