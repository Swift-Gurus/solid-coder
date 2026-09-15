"""Selects configured source-health checking for one prospective request."""

from hashlib import sha256
from pathlib import Path

from code_health_check_request import CodeHealthCheckRequest
from gate_logger import GateLogger
from hc_checker import HealthChecking
from hc_checker_factory import LegacyHealthCheckerFactory
from hc_config_schema import load_config
from hc_runner_factory import select_strategy
from health_check_mode import HealthCheckMode
from health_checker_creating import HealthCheckerCreating
from hook_utils import _resolve_project_root, solid_coder_project_dir
from json_serializer import JsonSerializer
from mcp_config_builder import McpConfigBuilder
from mcp_config_profile import McpConfigProfile
from utils.debug_logger import DebugLogger
from workflow_health_checker_factory import WorkflowHealthCheckerFactory


"""
solid-name: ConfiguredHealthCheckerFactory
solid-category: factory
solid-spec: [SPEC-050]
solid-description: Provides the configured source-health checker for a prospective request.
"""
class ConfiguredHealthCheckerFactory(HealthCheckerCreating):
    def __init__(self, plugin_root: Path) -> None:
        self._plugin_root = plugin_root

    def make(self, request: CodeHealthCheckRequest) -> HealthChecking:
        project_root = (
            Path(request.cwd).resolve()
            if request.cwd
            else _resolve_project_root().resolve()
        )
        config = load_config(project_root)
        strategy = select_strategy(config_loader=lambda: config)
        strategy.apply_env()
        mode = config.feature_flags.health_check_mode
        profile = (
            McpConfigProfile.LEGACY_HEALTH
            if mode is HealthCheckMode.LEGACY
            else McpConfigProfile.GATE_FLOW
        )
        mcp_config = McpConfigBuilder(
            project_root=self._plugin_root,
            profile=profile,
            serializer=JsonSerializer(),
        ).build()
        GateLogger(DebugLogger(
            project_dir_fn=lambda: solid_coder_project_dir(project_root),
            filename="gate.log",
        )).log(
            "health_check_mode="
            f"{mode.value} backend={config.llm.backend} model={config.llm.model} "
            f"target={request.path} source_sha256="
            f"{sha256(request.content.encode('utf-8')).hexdigest()}"
        )
        factory = (
            LegacyHealthCheckerFactory(
                project_root=project_root,
                config=config,
                strategy=strategy,
                mcp_config=mcp_config,
            )
            if mode is HealthCheckMode.LEGACY
            else WorkflowHealthCheckerFactory(
                plugin_root=self._plugin_root,
                project_root=project_root,
                config=config,
                strategy=strategy,
                mcp_config=mcp_config,
            )
        )
        return factory.make(request)
