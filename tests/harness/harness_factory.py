"""
solid-name: HarnessFactory
solid-category: service
solid-spec: [SPEC-014]
solid-description: Assembles a ready-to-run principle compliance test harness configured for a given project root and principle folder.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _HARNESS_DIR.parents[1]
_MCP_SERVER = _PROJECT_ROOT / "mcp-server"
_MCP_HEALTH = _MCP_SERVER / "health"
for _d in (
    str(_HARNESS_DIR),
    str(_MCP_SERVER),
    str(_MCP_SERVER / "utils"),
    str(_MCP_SERVER / "output"),
    str(_MCP_SERVER / "gate"),
    str(_MCP_SERVER / "patch"),
    str(_MCP_SERVER / "session"),
    str(_MCP_HEALTH),
    str(_MCP_HEALTH / "config"),
    str(_MCP_HEALTH / "llm"),
    str(_MCP_HEALTH / "codex"),
):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import hook_utils  # noqa: E402
from code_health_check_request import CodeHealthCheckRequest  # noqa: E402
from hc_checker import HealthChecking  # noqa: E402
from hc_checker_factory import LegacyHealthCheckerFactory  # noqa: E402
from hc_config_schema import load_config  # noqa: E402
from hc_runner_factory import select_strategy  # noqa: E402
from patch_review_context import PatchReviewContext  # noqa: E402

from apply_flow_invoker import ApplyFlowInvoker, ConfiguredReviewSessionRunner, FindingsReader, ReasoningWriter, ReviewArtifactHandler, ReviewInputBuilder  # noqa: E402
from expectation_loader import ExpectationLoader  # noqa: E402
from finding_comparer import FindingComparer, FlowFindingNormalizer  # noqa: E402
from fixture_discovery import FixtureDiscovery  # noqa: E402
from health_flow_invoker import CheckResultWriter, HealthFlowInvoker, SupportedExtensionsProvider  # noqa: E402
from interfaces import TimestampGenerating, TomlLoading  # noqa: E402
from mcp_utils import McpConfigBuilder  # noqa: E402
from metric_prefix_resolver import MetricPrefixResolver  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402
from output_path_builder import OutputPathBuilder  # noqa: E402
from path_resolver import PathResolver  # noqa: E402
from result_formatter import ResultFormatter  # noqa: E402
from test_harness_runner import TestHarnessRunner  # noqa: E402

import code_health_check  # noqa: E402


class HookUtilsTomlLoader(TomlLoading):
    def load_toml(self, path: Path) -> dict:
        return hook_utils.load_toml(path)


class RunTimestampGenerator(TimestampGenerating):
    def now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


class DirectHealthChecker(HealthChecking):
    """Constructs the legacy checker per call so model-profile overrides remain live."""

    def __init__(self, plugin_root: Path, project_root: Path) -> None:
        self._plugin_root = plugin_root
        self._project_root = project_root

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
        cwd: str = "",
        patch_context: PatchReviewContext | None = None,
        principle_names: list[str] | None = None,
    ):
        request = CodeHealthCheckRequest(
            content=content,
            path=path,
            language=language,
            parent_session_id=parent_session_id,
            cwd=cwd or str(self._project_root),
            patch_context=patch_context,
            principle_names=principle_names or [],
        )
        config = load_config(self._project_root)
        strategy = select_strategy(config_loader=lambda: config)
        strategy.apply_env()
        return LegacyHealthCheckerFactory(
            project_root=self._project_root,
            config=config,
            strategy=strategy,
            mcp_config=McpConfigBuilder().build(self._plugin_root),
        ).make(request).check(
            content,
            path,
            language,
            parent_session_id,
            patch_context=patch_context,
            principle_names=principle_names,
        )


class HarnessFactory:
    def build(
        self,
        project_root: Path,
        principle_folder: Path,
        profile_dir: "Path | None" = None,
    ) -> TestHarnessRunner:
        toml_loader = HookUtilsTomlLoader()
        mcp_config_builder = McpConfigBuilder()

        artifact_handler = ReviewArtifactHandler(
            input_builder=ReviewInputBuilder(),
            reasoning_writer=ReasoningWriter(),
            findings_reader=FindingsReader(),
        )
        session_runner = ConfiguredReviewSessionRunner(project_root, mcp_config_builder)
        apply_invoker = ApplyFlowInvoker(principle_folder, artifact_handler, session_runner)

        health_checker = DirectHealthChecker(
            plugin_root=project_root,
            project_root=project_root,
        )
        health_invoker = HealthFlowInvoker(
            checker=health_checker,
            language_provider=SupportedExtensionsProvider(code_health_check.SUPPORTED_EXTENSIONS),
            result_writer=CheckResultWriter(),
            principle_name=MetricPrefixResolver().resolve(principle_folder),
        )

        return TestHarnessRunner(
            path_resolver=PathResolver(project_root),
            fixture_discovery=FixtureDiscovery(),
            expectation_loader=ExpectationLoader(),
            model_profile_loader=ModelProfileLoader(project_root, toml_loader, profile_dir),
            output_path_builder=OutputPathBuilder(project_root),
            finding_comparer=FindingComparer(),
            finding_normalizer=FlowFindingNormalizer(),
            result_formatter=ResultFormatter(),
            apply_invoker=apply_invoker,
            health_invoker=health_invoker,
            timestamp_generator=RunTimestampGenerator(),
        )
