"""Composes production workflow include resolution."""

from harness.catalog_rule_set_members_resolver import CatalogRuleSetMembersResolver
from harness.condition_conjoiner import ConditionConjoiner
from harness.condition_serializer_factory import make_condition_serializer
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_cycle_guard import IncludeCycleGuard
from harness.include_resolution_merger import IncludeResolutionMerger
from harness.include_resolver import IncludeResolver
from harness.include_source_expansion_preparer import IncludeSourceExpansionPreparer
from harness.include_source_resolver import IncludeSourceResolver
from harness.include_step_appender import IncludeStepAppender
from harness.include_traverser import IncludeTraverser
from harness.inline_group_source_resolver import InlineGroupSourceResolver
from harness.nested_include_qualifier import NestedIncludeQualifier
from harness.nested_include_resolution_merger import NestedIncludeResolutionMerger
from harness.ordered_string_collector import OrderedStringCollector
from harness.path_building import PathBuilding
from harness.path_canonicalizer import PathCanonicalizer
from harness.path_include_source_resolver import PathIncludeSourceResolver
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.rule_match_condition_compiler import RuleMatchConditionCompiler
from harness.rule_selection_condition_compiler import RuleSelectionConditionCompiler
from harness.rule_set_include_reference import RuleSetIncludeReference
from harness.rule_set_include_reference_parser import RuleSetIncludeReferenceParser
from harness.rule_set_include_source_resolver import RuleSetIncludeSourceResolver
from harness.rule_set_member_serializer import RuleSetMemberSerializer
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.step_qualifier import StepQualifier
from harness.step_source_annotating import StepSourceAnnotating
from harness.workflow_catalog_resolving import WorkflowCatalogResolving
from harness.workflow_config_resource_loading import WorkflowConfigResourceLoading
from harness.workflow_include_runtime_parsing import WorkflowIncludeRuntimeParsing
from harness.workflow_include_source_resolver import WorkflowIncludeSourceResolver
from harness.workflow_output_declaration_parser import WorkflowOutputDeclarationParser
from harness.workflow_resource_reference_creating import (
    WorkflowResourceReferenceCreating,
)
from scoring.yaml_config_file_loader import ConfigFileLoading


"""
solid-name: IncludeResolverFactory
solid-category: factory
solid-spec: [SPEC-027, SPEC-035, SPEC-039]
solid-description: Provides production workflow include resolvers.
"""
class IncludeResolverFactory:

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        resource_loader: WorkflowConfigResourceLoading,
        catalog_resolver: WorkflowCatalogResolving,
        source_annotator: StepSourceAnnotating,
        runtime_parser: WorkflowIncludeRuntimeParsing,
        path_builder: PathBuilding,
        subflow_reference_factory: WorkflowResourceReferenceCreating,
        output_parser: WorkflowOutputDeclarationParser,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._file_loader = file_loader
        self._resource_loader = resource_loader
        self._catalog_resolver = catalog_resolver
        self._source_annotator = source_annotator
        self._runtime_parser = runtime_parser
        self._path_builder = path_builder
        self._subflow_reference_factory = subflow_reference_factory
        self._output_parser = output_parser
        self._error_factory = error_factory

    def make(self) -> IncludeResolver:
        resolution_merger = IncludeResolutionMerger(
            step_appender=IncludeStepAppender(),
            nested_merger=NestedIncludeResolutionMerger(
                ordered_strings=OrderedStringCollector(),
            ),
        )
        return IncludeResolver(
            path_canonicalizer=PathCanonicalizer(self._path_builder),
            traverser=IncludeTraverser(
                source_resolver=IncludeSourceResolver(
                    resolvers=[
                        RuleSetIncludeSourceResolver(
                            reference_parser=RuleSetIncludeReferenceParser(
                                PydanticModelDecoder(
                                    model_type=RuleSetIncludeReference,
                                )
                            ),
                            runtime_parser=self._runtime_parser,
                            members_resolver=CatalogRuleSetMembersResolver(
                                catalog_resolver=self._catalog_resolver,
                                match_compiler=RuleMatchConditionCompiler(
                                    RuleSelectionConditionCompiler()
                                ),
                                condition_conjoiner=ConditionConjoiner(),
                            ),
                            member_serializer=RuleSetMemberSerializer(
                                make_condition_serializer()
                            ),
                        ),
                        WorkflowIncludeSourceResolver(
                            file_loader=self._file_loader,
                            catalog_resolver=self._catalog_resolver,
                            source_annotator=self._source_annotator,
                            runtime_parser=self._runtime_parser,
                            output_parser=self._output_parser,
                            error_factory=self._error_factory,
                        ),
                        PathIncludeSourceResolver(
                            declaring_file_resolver=StepDeclaringFileResolver(
                                self._path_builder
                            ),
                            resource_loader=self._resource_loader,
                            reference_factory=self._subflow_reference_factory,
                            source_annotator=self._source_annotator,
                            runtime_parser=self._runtime_parser,
                            output_parser=self._output_parser,
                            error_factory=self._error_factory,
                        ),
                        InlineGroupSourceResolver(
                            self._source_annotator,
                            self._error_factory,
                        ),
                    ],
                    error_factory=self._error_factory,
                ),
                expansion_preparer=IncludeSourceExpansionPreparer(
                    IncludeCycleGuard(self._error_factory)
                ),
                nested_qualifier=NestedIncludeQualifier(
                    step_qualifier=StepQualifier(),
                ),
                resolution_merger=resolution_merger,
            ),
        )
