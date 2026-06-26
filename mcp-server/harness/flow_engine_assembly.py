"""
solid-description: Provides a flow engine assembly for executing flows.
solid-category: service
"""

from __future__ import annotations

from dataclasses import dataclass

from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader

from harness.dag_runner import DAGRunner
from harness.dag_running import DAGRunning
from harness.data_output_validator import DataOutputValidator
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
from harness.interpolator import Interpolator, TemplateRendering
from harness.json_loading import JsonLoader
from harness.json_schema_validating import JsonSchemaValidator
from harness.output_validating import OutputValidating
from harness.path_checking import PathChecker
from harness.schema_resolving import SchemaResolver
from harness.schema_validator import SchemaValidator
from harness.step_builder import StepBuilder
from harness.uses_resolver import UsesResolver


@dataclass(frozen=True)
class FlowEngineAssembly:
    """
    solid-description: Provides the configured components required to execute a flow.
    solid-category: service
    """

    flow_loader: FlowLoading
    event_appender: EventAppending
    event_replayer: EventReplayer
    dag_runner: DAGRunning
    interpolator: TemplateRendering
    schema_validator: SchemaValidator


def build_default_assembly() -> FlowEngineAssembly:
    """Construct and wire all flow engine components with production defaults."""
    yaml_loader = PyYamlLoader()
    yaml_file_loader = YamlConfigFileLoader(loader=yaml_loader)
    json_file_loader = YamlConfigFileLoader(loader=JsonLoader())

    resolver: ExpressionEvaluating = ExpressionResolver(filter_resolver=FilterResolver())
    interpolator = Interpolator(evaluator=resolver)

    flow_loader = FlowLoader(
        file_loader=yaml_file_loader,
        config_extractor=FlowConfigExtractor(),
        uses_resolver=UsesResolver(file_loader=yaml_file_loader),
        graph_validator=FlowGraphValidator(),
        step_builder=StepBuilder(),
    )

    event_appender = EventAppender(
        serializer=EventSerializer(),
        file_appender=POSIXFileAppender(),
    )
    event_replayer = EventReplayer(parser=EventParser())
    dag_runner = DAGRunner(renderer=interpolator, evaluator=resolver)

    validators: dict[str, OutputValidating] = {
        "file": FileOutputValidator(path_checker=PathChecker()),
        "data": DataOutputValidator(
            schema_resolver=SchemaResolver(file_loader=json_file_loader),
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
