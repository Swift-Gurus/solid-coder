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
_HOOKS_DIR = _PROJECT_ROOT / "hooks"
_MCP_HEALTH = _PROJECT_ROOT / "mcp-server" / "health"
for _d in (
    str(_HARNESS_DIR),
    str(_HOOKS_DIR),
    str(_HOOKS_DIR / "utils"),
    str(_HOOKS_DIR / "output"),
    str(_HOOKS_DIR / "gate"),
    str(_HOOKS_DIR / "patch"),
    str(_HOOKS_DIR / "session"),
    str(_MCP_HEALTH),
    str(_MCP_HEALTH / "config"),
    str(_MCP_HEALTH / "llm"),
    str(_MCP_HEALTH / "codex"),
):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import hook_utils  # noqa: E402
from hc_checker import HealthChecking  # noqa: E402
from hc_checker_factory import make_health_checker  # noqa: E402
from hook_callable import CallableAdapting  # noqa: E402

from apply_flow_invoker import ApplyFlowInvoker, ClaudeReviewSessionRunner, FindingsReader, ReasoningWriter, ReviewArtifactHandler, ReviewInputBuilder  # noqa: E402
from expectation_loader import ExpectationLoader  # noqa: E402
from finding_comparer import FindingComparer, FlowFindingNormalizer  # noqa: E402
from fixture_discovery import FixtureDiscovery  # noqa: E402
from health_flow_invoker import CheckResultWriter, HealthFlowInvoker, SupportedExtensionsProvider  # noqa: E402
from interfaces import ClaudeRunning, TimestampGenerating, TomlLoading  # noqa: E402
from mcp_utils import McpConfigBuilder, build_mcp_config  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402
from output_path_builder import OutputPathBuilder  # noqa: E402
from path_resolver import PathResolver  # noqa: E402
from result_formatter import ResultFormatter  # noqa: E402
from test_harness_runner import TestHarnessRunner  # noqa: E402

import code_health_check  # noqa: E402


class HookUtilsTomlLoader(TomlLoading):
    def load_toml(self, path: Path) -> dict:
        return hook_utils.load_toml(path)


class HookUtilsClaudeRunner(ClaudeRunning):
    def run_bare(
        self,
        prompt: str,
        allowed_tools: str,
        mcp_config: str,
        timeout: int,
        session_id: str,
        cwd: str,
        model: str,
    ) -> str | None:
        return hook_utils.run_claude_bare(
            prompt=prompt,
            allowed_tools=allowed_tools,
            mcp_config=mcp_config,
            timeout=timeout,
            session_id=session_id,
            cwd=cwd,
            model=model,
        )


class RunTimestampGenerator(TimestampGenerating):
    def now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


class DirectHealthChecker(HealthChecking):
    """Calls code_health_check._check() on every invocation so it reads
    hc_config (including SOLID_CODER_TEST_MODEL_PROFILE) at runtime rather
    than baking in the backend at construction time.
    """

    def __init__(self, checker_factory=None) -> None:
        self._checker_factory = checker_factory or code_health_check._check

    def check(self, content: str, path: str, language: str, parent_session_id: str):
        return self._checker_factory(content, path, language, parent_session_id)


class HarnessFactory:
    def build(
        self,
        project_root: Path,
        principle_folder: Path,
        profile_dir: "Path | None" = None,
    ) -> TestHarnessRunner:
        toml_loader = HookUtilsTomlLoader()
        claude_runner = HookUtilsClaudeRunner()
        mcp_config_builder = McpConfigBuilder()

        artifact_handler = ReviewArtifactHandler(
            input_builder=ReviewInputBuilder(),
            reasoning_writer=ReasoningWriter(),
            findings_reader=FindingsReader(),
        )
        session_runner = ClaudeReviewSessionRunner(project_root, claude_runner, mcp_config_builder)
        apply_invoker = ApplyFlowInvoker(principle_folder, artifact_handler, session_runner)

        health_checker = DirectHealthChecker()
        health_invoker = HealthFlowInvoker(
            checker=health_checker,
            language_provider=SupportedExtensionsProvider(code_health_check.SUPPORTED_EXTENSIONS),
            result_writer=CheckResultWriter(),
            principle_name=principle_folder.name,
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
