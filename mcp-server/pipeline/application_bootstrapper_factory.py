"""Assembles the production pipeline application."""

import importlib
from pathlib import Path
from typing import Optional

from findings.gateway_handler import GatewayHandling
from health.dry_search_service_factory import DrySearchServiceFactory
from lib.gateway_tools import GatewayHandlerFactory
from mcp_server_factory import MCPServerFactory
from message_transport_running import MessageTransportRunning
from pipeline.check_severity_running import CheckSeverityRunning
from pipeline.application_bootstrapper_creating import ApplicationBootstrapperCreating
from pipeline.context_loading import ContextLoading
from pipeline.flow_result_renderer_creating import FlowResultRendererCreating
from pipeline.flow_run_creating import FlowRunCreating
from pipeline.flow_tool_callables_assembler import FlowToolCallablesAssembler
from pipeline.handlers import make_review_results_collector
from pipeline.interfaces import ReviewResultsCollecting
from pipeline.output_path_factory import OutputPathFactory
from pipeline.output_validating import OutputValidating
from pipeline.pipeline_tool_callables_assembler import PipelineToolCallablesAssembler
from pipeline.pipeline_tool_callables_creating import PipelineToolCallablesCreating
from pipeline.server import ApplicationBootstrapper
from pipeline.skill_runner import ResultFormatting, SkillRunning, SkillResultFormatter, SkillRunner
from pipeline.tool_registry import ToolRegistering, ToolRegistry
from pipeline.tool_callables_building import ToolCallablesBuilding
from search.tag_codebase_searching import TagCodebaseSearching


"""
solid-name: ApplicationBootstrapperFactory
solid-category: factory
solid-description: Assembles the production pipeline application from configurable runtime services.
"""
class ApplicationBootstrapperFactory(
    ApplicationBootstrapperCreating,
    PipelineToolCallablesCreating,
):
    def __init__(
        self,
        plugin_root: Path,
        skills_root: Path,
        flow_run_creator: FlowRunCreating,
        flow_renderer_creator: FlowResultRendererCreating,
        server: Optional[MessageTransportRunning] = None,
        registry: Optional[ToolRegistering] = None,
        skill_runner: Optional[SkillRunning] = None,
        result_formatter: Optional[ResultFormatting] = None,
        collector: Optional[ReviewResultsCollecting] = None,
        gateway: Optional[GatewayHandling] = None,
        check_severity: Optional[CheckSeverityRunning] = None,
        context_loader: Optional[ContextLoading] = None,
        output_validator: Optional[OutputValidating] = None,
        search: Optional[TagCodebaseSearching] = None,
    ) -> None:
        self._plugin_root = plugin_root
        self._skills_root = skills_root
        self._flow_run_creator = flow_run_creator
        self._flow_renderer_creator = flow_renderer_creator
        self._server = server
        self._registry = registry
        self._skill_runner = skill_runner
        self._result_formatter = result_formatter
        self._collector = collector
        self._gateway = gateway
        self._check_severity = check_severity
        self._context_loader = context_loader
        self._output_validator = output_validator
        self._search = search

    def make(self) -> ApplicationBootstrapper:
        server = self._server or MCPServerFactory().build(
            "solid-coder-pipeline", "1.0.0"
        )
        return ApplicationBootstrapper(
            server=server,
            registry=self._registry or ToolRegistry(server),
            tool_callables=self.make_tool_callables(),
            flow_callables=FlowToolCallablesAssembler(
                flow_run=self._flow_run_creator.create(server),
                result_renderer=self._flow_renderer_creator.create(),
            ),
        )

    def make_tool_callables(self) -> ToolCallablesBuilding:
        runner = self._skill_runner or SkillRunner(self._skills_root)
        formatter = self._result_formatter or SkillResultFormatter()
        collector = self._collector or make_review_results_collector()
        gateway = self._gateway or GatewayHandlerFactory(
            batch_decorator=DrySearchServiceFactory()
        ).make(self._plugin_root / "references")
        severity = self._check_severity or importlib.import_module("check-severity")
        context = self._context_loader or importlib.import_module("load-context")
        validator = self._output_validator or importlib.import_module("validate-output")
        search = self._search or importlib.import_module("search.codebase_searcher")
        return PipelineToolCallablesAssembler(
            runner=runner,
            formatter=formatter,
            dry_search=DrySearchServiceFactory().make_search(search),
            collect_review_results=collector.collect,
            check_severity=severity.check_severity,
            load_context=context.load_context,
            validate_json=validator.validate_json,
            submit_findings=gateway.submit_findings,
            submit_batch_findings=gateway.submit_batch_findings,
            submit_fix=gateway.submit_fix,
            output_path=OutputPathFactory(),
            skills_root=self._skills_root,
            plugin_root=self._plugin_root,
        )
