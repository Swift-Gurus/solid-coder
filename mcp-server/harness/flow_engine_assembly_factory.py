"""Assembles a fully configured flow execution engine."""

from __future__ import annotations

from typing import Optional

from harness.agent_step_shape_validator import AgentStepShapeValidator
from harness.command_allowlist_resolver import CommandAllowlistResolver
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.dag_runner import DAGRunner
from harness.data_output_validator import DataOutputValidator
from harness.delegate_step_shape_validator import DelegateStepShapeValidator
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
from harness.flow_graph_validator import FlowGraphValidator
from harness.flow_loader import FlowLoader
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.group_dependency_expander import GroupDependencyExpander
from harness.include_cycle_guard import IncludeCycleGuard
from harness.include_resolver import IncludeResolver
from harness.include_source_resolver import IncludeSourceResolver
from harness.include_source_factory import IncludeSourceFactory
from harness.include_structure_validator import IncludeStructureValidator
from harness.inline_group_source_resolver import InlineGroupSourceResolver
from harness.interpolator import Interpolator
from harness.json_loading import JsonLoader
from harness.json_schema_validating import JsonSchemaValidator
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.output_schema_declaration_validator import OutputSchemaDeclarationValidator
from harness.output_collection_resolver import OutputCollectionResolver
from harness.output_schema_file_loader import OutputSchemaFileLoader
from harness.output_schema_prompt_annotator import OutputSchemaPromptAnnotator
from harness.output_schema_reference_resolver import OutputSchemaReferenceResolver
from harness.output_schema_resolver import OutputSchemaResolver
from harness.output_validating import OutputValidating
from harness.path_builder import PathBuilder
from harness.path_checking import PathChecker
from harness.path_include_source_resolver import PathIncludeSourceResolver
from harness.prompt_content_resolver import PromptContentResolver
from harness.prompt_file_loader import PromptFileLoader
from harness.prompt_file_path_resolver import PromptFilePathResolver
from harness.run_state_reconstructor_factory import make_run_state_reconstructor
from harness.schema_resolving import SchemaResolver
from harness.schema_validator import SchemaValidator
from harness.script_step_shape_validator import ScriptStepShapeValidator
from harness.step_builder import StepBuilder
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.step_graph_validator import StepGraphValidator
from harness.step_shape_validator import StepShapeValidator
from harness.step_qualifier import StepQualifier
from harness.step_source_annotator import StepSourceAnnotator
from harness.uses_resolver import UsesResolver
from harness.workflow_catalog_resolving import WorkflowCatalogResolving
from harness.workflow_catalog_factory import make_workflow_catalog_resolver
from harness.workflow_include_source_resolver import WorkflowIncludeSourceResolver
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: FlowEngineAssemblyFactory
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Constructs a flow-engine assembly from optional command and workflow catalog configuration.
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
        resource_path_resolver = WorkflowResourcePathResolver(
            package_root_locator=package_root_locator
        )
        source_annotator = StepSourceAnnotator()
        include_source_factory = IncludeSourceFactory()

        expression_resolver: ExpressionEvaluating = ExpressionResolver(
            filter_resolver=FilterResolver()
        )
        interpolator = Interpolator(evaluator=expression_resolver)
        cycle_detector = KahnCycleDetector()
        graph_validator = FlowGraphValidator(
            step_graph_validator=StepGraphValidator(cycle_detector=cycle_detector),
            include_structure_validator=IncludeStructureValidator(cycle_detector=cycle_detector),
            for_each_validator=ForEachReferenceValidator(),
        )

        uses_resolver = UsesResolver(
                file_loader=yaml_file_loader,
                resource_path_resolver=resource_path_resolver,
                package_root_locator=package_root_locator,
                path_builder=path_builder,
                error_factory=error_factory,
            )
        include_resolver = IncludeResolver(
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
                            file_loader=yaml_file_loader,
                            declaring_file_resolver=StepDeclaringFileResolver(path_builder),
                            resource_path_resolver=resource_path_resolver,
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
                cycle_guard=IncludeCycleGuard(error_factory),
                step_qualifier=StepQualifier(),
            )
        prompt_resolver = PromptContentResolver(
            path_resolver=PromptFilePathResolver(
                path_builder=path_builder,
                resource_path_resolver=resource_path_resolver,
            ),
            prompt_loader=PromptFileLoader(
                reader=PlainTextFileReader(),
                error_factory=error_factory,
            ),
        )
        schema_resolver = OutputSchemaResolver(
            declaring_file_resolver=StepDeclaringFileResolver(path_builder),
            output_collection_resolver=OutputCollectionResolver(
                schema_reference_resolver=OutputSchemaReferenceResolver(
                    declaration_validator=OutputSchemaDeclarationValidator(error_factory),
                    schema_loader=OutputSchemaFileLoader(
                        file_loader=json_file_loader,
                        resource_path_resolver=resource_path_resolver,
                        error_factory=error_factory,
                    ),
                )
            ),
        )
        flow_loader = FlowLoader(
            file_loader=yaml_file_loader,
            definition_resolver=FlowDefinitionResolver(
                config_extractor=FlowConfigExtractor(),
                source_annotator=source_annotator,
                uses_resolver=uses_resolver,
                include_resolver=include_resolver,
                prompt_resolver=prompt_resolver,
                schema_resolver=schema_resolver,
                prompt_annotator=OutputSchemaPromptAnnotator(),
            ),
            definition_validator=FlowDefinitionValidator(
                step_shape_validator=StepShapeValidator(
                validators={
                    "agent": AgentStepShapeValidator(),
                    "script": ScriptStepShapeValidator(),
                    "delegate": DelegateStepShapeValidator(),
                },
                default=AgentStepShapeValidator(),
                ),
                command_allowlist_resolver=allowlist_resolver,
                command_allowlist_validator=CommandAllowlistValidator(),
                graph_validator=graph_validator,
            ),
            definition_assembler=FlowDefinitionAssembler(
                group_dependency_expander=GroupDependencyExpander(),
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
