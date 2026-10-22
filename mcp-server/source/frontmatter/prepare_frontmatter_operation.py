"""Prepares metadata review using authoritative declaration facts."""

from pathlib import Path

from findings.review_unit_kind import ReviewUnitKind
from harness.flow_validation_error import FlowValidationError
from harness.operation_handling import OperationHandling
from harness.project_context import ProjectDirectoryReading
from health.config.frontmatter_config import FrontmatterConfig
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.frontmatter.frontmatter_preparation import FrontmatterPreparation
from source.frontmatter.prepare_frontmatter_input import PrepareFrontmatterInput
from source.frontmatter.source_description_target import SourceDescriptionTarget
from source.frontmatter.source_frontmatter_inspection import SourceFrontmatterInspection
from source.frontmatter.stack_registration import StackRegistration
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_frontmatter import SourceFrontmatter
from source.technology_detection import TechnologyDetection


"""
solid-name: PrepareFrontmatterOperation
solid-category: service
solid-spec: [SPEC-069]
solid-description: Prepares source-owned metadata validity, structural exclusions, description targets and effective policy for auditable review.
"""
class PrepareFrontmatterOperation(OperationHandling[PrepareFrontmatterInput, FrontmatterPreparation]):
    def __init__(
        self,
        metadata: SourceSyntaxParsing[str, SourceFrontmatter | None],
        stacks: SourceSyntaxParsing[SourceAnalysis, list[TechnologyDetection]],
        configuration: SourceSyntaxParsing[Path, FrontmatterConfig],
        project_directory: ProjectDirectoryReading,
        stack_registrations: list[StackRegistration],
        categories: SourceSyntaxParsing[FrontmatterConfig, list[str]],
    ) -> None:
        self._metadata = metadata
        self._stacks = stacks
        self._configuration = configuration
        self._project_directory = project_directory
        self._stack_registrations = stack_registrations
        self._categories = categories

    def execute(self, operation_input: PrepareFrontmatterInput) -> FrontmatterPreparation:
        analysis = operation_input.analysis
        categories = self._categories.parse(self._configuration.parse(self._project_directory.read()))
        limitations = []
        if analysis.decision is not SourceAnalysisDecision.PARSED:
            limitations.append(f"Source analysis of {analysis.source_identity} is {analysis.decision.value}.")
            limitations.extend(diagnostic.message for diagnostic in analysis.diagnostics)
        stacks = self._stacks.parse(analysis)
        entries: list[SourceFrontmatterInspection] = []
        descriptions: list[SourceDescriptionTarget] = []
        for declaration in analysis.declarations:
            unit = declaration.unit
            if declaration.scope_kind is not SourceScopeKind.FILE or not unit.kind.supports_member_declarations:
                continue
            try:
                metadata = self._metadata.parse("\n".join(comment.fact for comment in declaration.leading_comments))
            except FlowValidationError as error:
                limitations.append(f"{unit.name}, line {unit.span.start}: {error}")
                continue
            present = metadata is not None
            metadata = metadata if metadata is not None else SourceFrontmatter()
            evidence = [detection for detection in stacks if detection.scope_identity == unit.identity]
            bad_description = present and (
                not metadata.description.strip()
                or (metadata.category == "abstraction" and not metadata.description.startswith(("Contract for", "Contract that defines")))
            )
            entries.append(SourceFrontmatterInspection(
                declaration=declaration,
                metadata=metadata,
                has_frontmatter=present,
                missing_exempt=(
                    (any(modifier in {"private", "fileprivate"} for modifier in declaration.modifiers)
                     and unit.span.end - unit.span.start + 1 < 10)
                    or (unit.kind is ReviewUnitKind.EXTENSION and not unit.members)
                ),
                name_matches=metadata.name == unit.name,
                category_registered=metadata.category in categories,
                stack_matches=set(metadata.stack) == {detection.tag for detection in evidence},
                bad_description=bad_description,
                stack_evidence=evidence,
            ))
            if present and not bad_description:
                descriptions.append(SourceDescriptionTarget(
                    declaration_id=declaration.identity,
                    name=unit.name,
                    label=f"{unit.name} (line {unit.span.start})",
                    category=metadata.category,
                    description=metadata.description,
                ))
        return FrontmatterPreparation(
            entries=entries,
            descriptions=descriptions,
            categories=categories,
            stack_registrations=self._stack_registrations,
            limitations=limitations,
        )
