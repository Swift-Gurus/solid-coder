"""
solid-description: Assembles a fully-configured flow execution engine.
solid-category: service
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader

from harness.agent_step_shape_validator import AgentStepShapeValidator
from harness.command_allowlist_resolver import CommandAllowlistResolver
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.dag_runner import DAGRunner
from harness.dag_running import DAGRunning
from harness.data_output_validator import DataOutputValidator
from harness.delegate_step_shape_validator import DelegateStepShapeValidator
from harness.event_appender import EventAppender, EventAppending, EventSerializer, POSIXFileAppender
from harness.event_replayer import EventParser, EventReplayer
from harness.file_output_validator import FileOutputValidator
from harness.flow_config_extractor import FlowConfigExtractor
from harness.flow_graph_validator import FlowGraphValidator
from harness.flow_loader import FlowLoader
from harness.flow_loading import FlowLoading
from harness.expression_evaluating import ExpressionEvaluating
from harness.expression_resolver import ExpressionResolver
from harness.filter_resolver import FilterResolver
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.group_dependency_expander import GroupDependencyExpander
from harness.include_resolver import IncludeResolver
from harness.include_structure_validator import IncludeStructureValidator
from harness.interpolator import Interpolator, TemplateRendering
from harness.json_loading import JsonLoader
from harness.json_schema_validating import JsonSchemaValidator
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.output_schema_prompt_annotator import OutputSchemaPromptAnnotator
from harness.output_schema_resolver import OutputSchemaResolver
from harness.output_validating import OutputValidating
from harness.path_checking import PathChecker
from harness.prompt_content_resolver import PromptContentResolver
from harness.run_state_reconstructor import RunStateReconstructor
from harness.schema_resolving import SchemaResolver
from harness.schema_validator import SchemaValidator
from harness.script_step_shape_validator import ScriptStepShapeValidator
from harness.step_builder import StepBuilder
from harness.step_graph_validator import StepGraphValidator
from harness.step_shape_validator import StepShapeValidator
from harness.uses_resolver import UsesResolver
from utils.prompt_builder import PlainTextFileReader


@dataclass(frozen=True)
class FlowEngineAssembly:
    """
    solid-description: Provides flow loading, execution, and event management services.
    solid-category: service
    """

    flow_loader: FlowLoading
    event_appender: EventAppending
    event_replayer: EventReplayer
    dag_runner: DAGRunning
    interpolator: TemplateRendering
    schema_validator: SchemaValidator


def build_default_assembly(
    command_allowlist_resolver: Optional[CommandAllowlistResolving] = None,
) -> FlowEngineAssembly:
    """Construct and wire all flow engine components with production defaults."""
    command_allowlist_resolver = command_allowlist_resolver or CommandAllowlistResolver()
    yaml_loader = PyYamlLoader()
    yaml_file_loader = YamlConfigFileLoader(loader=yaml_loader)
    json_file_loader = YamlConfigFileLoader(loader=JsonLoader())

    resolver: ExpressionEvaluating = ExpressionResolver(filter_resolver=FilterResolver())
    interpolator = Interpolator(evaluator=resolver)

    cycle_detector = KahnCycleDetector()
    graph_validator = FlowGraphValidator(
        step_graph_validator=StepGraphValidator(cycle_detector=cycle_detector),
        include_structure_validator=IncludeStructureValidator(cycle_detector=cycle_detector),
        for_each_validator=ForEachReferenceValidator(),
    )

    flow_loader = FlowLoader(
        file_loader=yaml_file_loader,
        config_extractor=FlowConfigExtractor(),
        uses_resolver=UsesResolver(file_loader=yaml_file_loader),
        graph_validator=graph_validator,
        step_builder=StepBuilder(),
        include_resolver=IncludeResolver(file_loader=yaml_file_loader),
        step_shape_validator=StepShapeValidator(
            validators={
                "agent": AgentStepShapeValidator(),
                "script": ScriptStepShapeValidator(),
                "delegate": DelegateStepShapeValidator(),
            },
            default=AgentStepShapeValidator(),
        ),
        prompt_content_resolver=PromptContentResolver(reader=PlainTextFileReader()),
        output_schema_resolver=OutputSchemaResolver(file_loader=json_file_loader),
        output_schema_prompt_annotator=OutputSchemaPromptAnnotator(),
        command_allowlist_resolver=command_allowlist_resolver,
        command_allowlist_validator=CommandAllowlistValidator(),
        group_dependency_expander=GroupDependencyExpander(),
    )

    event_appender = EventAppender(
        serializer=EventSerializer(),
        file_appender=POSIXFileAppender(),
    )
    event_replayer = EventReplayer(parser=EventParser(), reconstructor=RunStateReconstructor())
    dag_runner = DAGRunner(renderer=interpolator, evaluator=resolver)

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
        dag_runner=dag_runner,
        interpolator=interpolator,
        schema_validator=SchemaValidator(validators=validators),
    )
