"""Selects configured source-health checking for one prospective request."""

from hashlib import sha256
from pathlib import Path

from code_health_check_request import CodeHealthCheckRequest
from gate_logger import GateLogger
from hc_checker import HealthChecking
from hc_checker_factory import LegacyHealthCheckerFactory
from hc_runner_factory import select_strategy
from health.config.hc_config_core import find_repository_root
from health_check_mode import HealthCheckMode
from health_check_outcome import HealthCheckOutcome
from health_checker_creating import HealthCheckerCreating
from hook_utils import _resolve_project_root, solid_coder_project_dir
from json_serializer import JsonSerializer
from legacy_health_outcome_adapter import LegacyHealthOutcomeAdapter
from mcp_config_builder import McpConfigBuilder
from mcp_config_profile import McpConfigProfile
from solid_coder_config_loader import SolidCoderConfigLoader
from source.repository_target_resolver import RepositoryTargetResolver
from utils.debug_logger import DebugLogger
from workflow_health_checker_factory import WorkflowHealthCheckerFactory

"""
solid-name: ConfiguredHealthCheckerFactory
solid-category: factory
solid-spec: [SPEC-050]
solid-description: Provides the configured source-health checker for a prospective request.
"""


class ConfiguredHealthCheckerFactory(HealthCheckerCreating[HealthCheckOutcome]):
    def __init__(self, plugin_root: Path) -> None:
        self._plugin_root = plugin_root

    def make(
        self, request: CodeHealthCheckRequest
    ) -> HealthChecking[HealthCheckOutcome]:
        effective_cwd = (
            Path(request.cwd).resolve()
            if request.cwd
            else _resolve_project_root().resolve()
        )
        project_root = RepositoryTargetResolver(find_repository_root).resolve(
            effective_cwd, Path(".")
        )
        config = SolidCoderConfigLoader().load(effective_cwd)
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
        GateLogger(
            DebugLogger(
                project_dir_fn=lambda: solid_coder_project_dir(project_root),
                filename="gate.log",
            )
        ).log(
            "health_check_mode="
            f"{mode.value} backend={config.llm.backend} model={config.llm.model} "
            f"target={request.path} source_sha256="
            f"{sha256(request.content.encode('utf-8')).hexdigest()}"
        )
        if mode is HealthCheckMode.LEGACY:
            return LegacyHealthOutcomeAdapter(
                LegacyHealthCheckerFactory(
                    project_root=project_root,
                    config=config,
                    strategy=strategy,
                    mcp_config=mcp_config,
                ).make(request)
            )
        return WorkflowHealthCheckerFactory(
            plugin_root=self._plugin_root,
            project_root=project_root,
            config=config,
            strategy=strategy,
            mcp_config=mcp_config,
        ).make(request)
