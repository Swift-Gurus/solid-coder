"""Assembles a fully configured flow execution engine."""

from __future__ import annotations

from typing import Optional

from harness.agent_step_shape_validator import AgentStepShapeValidator
from harness.command_allowlist_resolver import CommandAllowlistResolver
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.command_step_shape_validator import CommandStepShapeValidator
from harness.command_step_value_validator import CommandStepValueValidator
from harness.dag_runner import DAGRunner
from harness.data_output_validator import DataOutputValidator
from harness.delegate_step_shape_validator import DelegateStepShapeValidator
from harness.directed_graph_factory import DirectedGraphFactory
from harness.event_appender import EventAppender, EventSerializer, POSIXFileAppender
from harness.event_replayer import EventParser, EventReplayer
from harness.expression_evaluating import ExpressionEvaluating
from harness.expression_resolver import ExpressionResolver
from harness.file_output_validator import FileOutputValidator
from harness.filter_resolver import FilterResolver
from harness.flow_config_extractor import FlowConfigExtractor
from harness.flow_definition_assembler import FlowDefinitionAssembler
from harness.flow_definition_resolver import FlowDefinitionResolver
from harness.flow_definition_validator import FlowDefinitionValidator
from harness.flow_engine_assembly import FlowEngineAssembly
from harness.flow_loader import FlowLoader
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.group_dependency_expander import GroupDependencyExpander
from harness.include_alias_collision_validator import IncludeAliasCollisionValidator
from harness.include_alias_group_factory import IncludeAliasGroupFactory
from harness.include_alias_group_finder import IncludeAliasGroupFinder
from harness.include_cycle_guard import IncludeCycleGuard
from harness.include_cycle_validator import IncludeCycleValidator
from harness.include_group_membership_resolver import IncludeGroupMembershipResolver
from harness.include_group_opacity_validator import IncludeGroupOpacityValidator
from harness.include_resolution_merger import IncludeResolutionMerger
from harness.include_resolver import IncludeResolver
from harness.include_source_expansion_preparer import IncludeSourceExpansionPreparer
from harness.include_source_resolver import IncludeSourceResolver
from harness.include_source_factory import IncludeSourceFactory
from harness.include_step_appender import IncludeStepAppender
from harness.include_structure_validator import IncludeStructureValidator
from harness.include_traverser import IncludeTraverser
from harness.inline_group_source_resolver import InlineGroupSourceResolver
from harness.interpolator import Interpolator
from harness.incoming_edge_checker import IncomingEdgeChecker
from harness.json_loading import JsonLoader
from harness.json_schema_validating import JsonSchemaValidator
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.nested_include_qualifier import NestedIncludeQualifier
from harness.nested_include_resolution_merger import NestedIncludeResolutionMerger
from harness.ordered_string_collector import OrderedStringCollector
from harness.output_schema_declaration_validator import OutputSchemaDeclarationValidator
from harness.output_collection_resolver import OutputCollectionResolver
from harness.output_schema_file_loader import OutputSchemaFileLoader
from harness.output_schema_description_collector import OutputSchemaDescriptionCollector
from harness.output_schema_prompt_annotator import OutputSchemaPromptAnnotator
from harness.output_spec_factory import OutputSpecFactory
from harness.output_schema_reference_resolver import OutputSchemaReferenceResolver
from harness.output_schema_resolver import OutputSchemaResolver
from harness.output_validating import OutputValidating
from harness.path_builder import PathBuilder
from harness.path_canonicalizer import PathCanonicalizer
from harness.path_checking import PathChecker
from harness.path_include_source_resolver import PathIncludeSourceResolver
from harness.prompt_content_resolver import PromptContentResolver
from harness.prompt_file_loader import PromptFileLoader
from harness.prompt_file_path_resolver import PromptFilePathResolver
from harness.resolved_flow_definition_factory import ResolvedFlowDefinitionFactory
from harness.resolved_output_schema_applier import ResolvedOutputSchemaApplier
from harness.resolved_outputs_applier import ResolvedOutputsApplier
from harness.resolved_prompt_applier import ResolvedPromptApplier
from harness.resolved_script_file_applier import ResolvedScriptFileApplier
from harness.resolved_step_resources_applier import ResolvedStepResourcesApplier
from harness.resolved_step_resources_factory import ResolvedStepResourcesFactory
from harness.run_state_reconstructor_factory import make_run_state_reconstructor
from harness.schema_resolving import SchemaResolver
from harness.schema_validator import SchemaValidator
from harness.script_file_resolver import ScriptFileResolver
from harness.script_step_shape_validator import ScriptStepShapeValidator
from harness.script_step_value_validator import ScriptStepValueValidator
from harness.step_builder import StepBuilder
from harness.step_collection_uses_resolver import StepCollectionUsesResolver
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.step_declaration_factory import StepDeclarationFactory
from harness.step_dependency_graph_factory import StepDependencyGraphFactory
from harness.step_executable_resolver import StepExecutableResolver
from harness.step_field_validator_registration import StepFieldValidatorRegistration
from harness.step_graph_validator import StepGraphValidator
from harness.step_identity_resolver import StepIdentityResolver
from harness.step_prompt_augmenter import StepPromptAugmenter
from harness.step_shape_validator import StepShapeValidator
from harness.step_qualifier import StepQualifier
from harness.step_source_collector import StepSourceCollector
from harness.step_source_annotator import StepSourceAnnotator
from harness.uses_resolver import UsesResolver
from harness.unique_step_identity_validator import UniqueStepIdentityValidator
from harness.workflow_catalog_resolving import WorkflowCatalogResolving
from harness.workflow_catalog_factory import make_workflow_catalog_resolver
from harness.workflow_config_resource_loader import WorkflowConfigResourceLoader
from harness.workflow_include_source_resolver import WorkflowIncludeSourceResolver
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_path_classifier import WorkflowResourcePathClassifier
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver
from harness.workflow_resource_reference_factory import WorkflowResourceReferenceFactory
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader
from json_serializer import JsonSerializer
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: FlowEngineAssemblyFactory
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Provides a ready-to-use flow execution engine with workflow loading, validation, orchestration, and event services.
"""
class FlowEngineAssemblyFactory:
    def build(
        self,
        command_allowlist_resolver: Optional[CommandAllowlistResolving] = None,
        workflow_catalog_resolver: Optional[WorkflowCatalogResolving] = None,
    ) -> FlowEngineAssembly:
        allowlist_resolver = command_allowlist_resolver or CommandAllowlistResolver()
        catalog_resolver = workflow_catalog_resolver or make_workflow_catalog_resolver()
        yaml_file_loader = YamlConfigFileLoader(loader=PyYamlLoader())
        json_file_loader = YamlConfigFileLoader(loader=JsonLoader())
        path_builder = PathBuilder()
        error_factory = FlowValidationErrorFactory()
        package_root_locator = WorkflowPackageRootLocator()
        resource_path_classifier = WorkflowResourcePathClassifier()
        prompt_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.PROMPTS,
        )
        schema_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.SCHEMAS,
        )
        steps_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.STEPS,
        )
        subflow_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.SUBFLOWS,
        )
        script_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.SCRIPTS,
        )
        resource_path_resolver = WorkflowResourcePathResolver(
            package_root_locator=package_root_locator,
            error_factory=error_factory,
        )
        json_resource_loader = WorkflowConfigResourceLoader(
            file_loader=json_file_loader,
            path_resolver=resource_path_resolver,
        )
        yaml_resource_loader = WorkflowConfigResourceLoader(
            file_loader=yaml_file_loader,
            path_resolver=resource_path_resolver,
        )
        source_annotator = StepSourceAnnotator()
        include_source_factory = IncludeSourceFactory()

        expression_resolver: ExpressionEvaluating = ExpressionResolver(
            filter_resolver=FilterResolver()
        )
        interpolator = Interpolator(evaluator=expression_resolver)
        graph_factory = DirectedGraphFactory()
        cycle_detector = KahnCycleDetector(IncomingEdgeChecker())
        step_identity_resolver = StepIdentityResolver(error_factory)
        dependency_validator = StepGraphValidator(
            identity_validator=UniqueStepIdentityValidator(
                step_identity_resolver,
                error_factory,
            ),
            graph_factory=StepDependencyGraphFactory(
                identity_resolver=step_identity_resolver,
                graph_factory=graph_factory,
                error_factory=error_factory,
            ),
            cycle_detector=cycle_detector,
            error_factory=error_factory,
        )
        include_structure_validator = IncludeStructureValidator(
            alias_collision_validator=IncludeAliasCollisionValidator(error_factory),
            group_opacity_validator=IncludeGroupOpacityValidator(
                membership_resolver=IncludeGroupMembershipResolver(),
                error_factory=error_factory,
            ),
            include_cycle_validator=IncludeCycleValidator(
                graph_factory=graph_factory,
                cycle_detector=cycle_detector,
                error_factory=error_factory,
            ),
        )

        uses_resolver = UsesResolver(
                resource_loader=yaml_resource_loader,
                reference_factory=steps_reference_factory,
                package_root_locator=package_root_locator,
                path_builder=path_builder,
                error_factory=error_factory,
            )
        include_alias_group_factory = IncludeAliasGroupFactory()
        include_resolution_merger = IncludeResolutionMerger(
            step_appender=IncludeStepAppender(),
            nested_merger=NestedIncludeResolutionMerger(
                alias_group_factory=include_alias_group_factory,
                ordered_strings=OrderedStringCollector(),
            ),
        )
        include_resolver = IncludeResolver(
            path_canonicalizer=PathCanonicalizer(path_builder),
            traverser=IncludeTraverser(
                source_resolver=IncludeSourceResolver(
                    resolvers=[
                        WorkflowIncludeSourceResolver(
                            file_loader=yaml_file_loader,
                            catalog_resolver=catalog_resolver,
                            source_annotator=source_annotator,
                            error_factory=error_factory,
                            source_factory=include_source_factory,
                        ),
                        PathIncludeSourceResolver(
                            declaring_file_resolver=StepDeclaringFileResolver(path_builder),
                            resource_loader=yaml_resource_loader,
                            reference_factory=subflow_reference_factory,
                            source_annotator=source_annotator,
                            error_factory=error_factory,
                            source_factory=include_source_factory,
                        ),
                        InlineGroupSourceResolver(
                            source_annotator,
                            error_factory,
                            include_source_factory,
                        ),
                    ],
                    error_factory=error_factory,
                ),
                expansion_preparer=IncludeSourceExpansionPreparer(
                    IncludeCycleGuard(error_factory)
                ),
                nested_qualifier=NestedIncludeQualifier(
                    step_qualifier=StepQualifier(),
                    alias_group_factory=include_alias_group_factory,
                ),
                resolution_merger=include_resolution_merger,
            ),
        )
        step_resources_factory = ResolvedStepResourcesFactory()
        step_resources_applier = ResolvedStepResourcesApplier()
        prompt_resolver = PromptContentResolver(
            path_resolver=PromptFilePathResolver(
                path_builder=path_builder,
                resource_path_resolver=resource_path_resolver,
                reference_factory=prompt_reference_factory,
            ),
            prompt_loader=PromptFileLoader(
                reader=PlainTextFileReader(),
                error_factory=error_factory,
            ),
            prompt_applier=ResolvedPromptApplier(
                resources_factory=step_resources_factory,
                resources_applier=step_resources_applier,
            ),
        )
        output_spec_factory = OutputSpecFactory()
        schema_resolver = OutputSchemaResolver(
            declaring_file_resolver=StepDeclaringFileResolver(path_builder),
            output_collection_resolver=OutputCollectionResolver(
                schema_reference_resolver=OutputSchemaReferenceResolver(
                    declaration_validator=OutputSchemaDeclarationValidator(error_factory),
                    schema_loader=OutputSchemaFileLoader(
                        resource_loader=json_resource_loader,
                        reference_factory=schema_reference_factory,
                        error_factory=error_factory,
                    ),
                    schema_applier=ResolvedOutputSchemaApplier(
                        output_spec_factory
                    ),
                    identity_resolver=step_identity_resolver,
                )
            ),
            outputs_applier=ResolvedOutputsApplier(
                resources_factory=step_resources_factory,
                resources_applier=step_resources_applier,
            ),
        )
        flow_loader = FlowLoader(
            file_loader=yaml_file_loader,
            definition_resolver=FlowDefinitionResolver(
                config_extractor=FlowConfigExtractor(),
                path_builder=path_builder,
                source_annotator=source_annotator,
                source_collector=StepSourceCollector(),
                uses_resolver=StepCollectionUsesResolver(uses_resolver),
                include_resolver=include_resolver,
                script_file_resolver=ScriptFileResolver(
                    declaring_file_resolver=StepDeclaringFileResolver(path_builder),
                    resource_path_resolver=resource_path_resolver,
                    reference_factory=script_reference_factory,
                    script_file_applier=ResolvedScriptFileApplier(
                        resources_factory=step_resources_factory,
                        resources_applier=step_resources_applier,
                    ),
                ),
                prompt_resolver=prompt_resolver,
                schema_resolver=schema_resolver,
                prompt_annotator=OutputSchemaPromptAnnotator(
                    description_collector=OutputSchemaDescriptionCollector(
                        JsonSerializer()
                    ),
                    prompt_augmenter=StepPromptAugmenter(),
                ),
                step_mapper=StepDeclarationFactory(output_spec_factory),
                definition_factory=ResolvedFlowDefinitionFactory(),
            ),
            definition_validator=FlowDefinitionValidator(
                step_shape_validator=StepShapeValidator(
                    registrations=[
                        StepFieldValidatorRegistration(
                            "agent",
                            AgentStepShapeValidator(error_factory),
                        ),
                        StepFieldValidatorRegistration(
                            "script",
                            ScriptStepShapeValidator(
                                ScriptStepValueValidator(error_factory),
                                error_factory,
                            ),
                        ),
                        StepFieldValidatorRegistration(
                            "command",
                            CommandStepShapeValidator(
                                CommandStepValueValidator(error_factory),
                                error_factory,
                            ),
                        ),
                        StepFieldValidatorRegistration(
                            "delegate",
                            DelegateStepShapeValidator(error_factory),
                        ),
                    ],
                    default=AgentStepShapeValidator(error_factory),
                ),
                command_allowlist_resolver=allowlist_resolver,
                command_allowlist_validator=CommandAllowlistValidator(
                    executable_resolver=StepExecutableResolver(),
                    error_factory=error_factory,
                ),
                dependency_validator=dependency_validator,
                include_validator=include_structure_validator,
                for_each_validator=ForEachReferenceValidator(),
            ),
            definition_assembler=FlowDefinitionAssembler(
                group_dependency_expander=GroupDependencyExpander(
                    IncludeAliasGroupFinder()
                ),
                step_builder=StepBuilder(),
            ),
            error_factory=error_factory,
        )

        event_appender = EventAppender(
            serializer=EventSerializer(),
            file_appender=POSIXFileAppender(),
        )
        event_replayer = EventReplayer(
            parser=EventParser(),
            reconstructor=make_run_state_reconstructor(),
        )
        validators: dict[str, OutputValidating] = {
            "file": FileOutputValidator(path_checker=PathChecker()),
            "data": DataOutputValidator(
                schema_resolver=SchemaResolver(),
                json_schema=JsonSchemaValidator(),
            ),
        }
        return FlowEngineAssembly(
            flow_loader=flow_loader,
            event_appender=event_appender,
            event_replayer=event_replayer,
            dag_runner=DAGRunner(renderer=interpolator, evaluator=expression_resolver),
            interpolator=interpolator,
            schema_validator=SchemaValidator(validators=validators),
        )
