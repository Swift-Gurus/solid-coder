"""
solid-description: Provides principle detection rules and candidate tags for automated code health analysis.
solid-category: service
solid-tags: [hook, gateway]
"""

import sys
from pathlib import Path
from typing import Callable, Optional, Protocol

_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import run_gateway_cmd
from hook_callable import CallableAdapting


class CommandRunning(Protocol):
    def run_cmd(self, cmd: list, timeout: int) -> Optional[dict]: ...


GatewayCallable = Callable[[list, int], Optional[dict]]


class GatewayCommandRunner(CallableAdapting):
    """Adapts a GatewayCallable to the CommandRunning protocol."""

    def __init__(self, fn: GatewayCallable = run_gateway_cmd) -> None:
        super().__init__(fn)

    def run_cmd(self, cmd: list, timeout: int) -> Optional[dict]:
        return self._fn(cmd, timeout)


class GatewayInvoking(Protocol):
    def invoke(
        self,
        subcommand: str,
        extra_args: Optional[list],
        timeout: int,
        result_key: Optional[str],
        default,
    ): ...


class GatewayInvoker:
    """Builds and executes gateway CLI commands. Shared by all gateway-backed components."""

    def __init__(self, gateway: Path, runner: CommandRunning) -> None:
        self._gateway = gateway
        self._runner = runner

    def invoke(
        self,
        subcommand: str,
        extra_args: Optional[list] = None,
        timeout: int = 10,
        result_key: Optional[str] = None,
        default=None,
    ):
        cmd = ["python3", str(self._gateway), subcommand] + (extra_args or [])
        data = self._runner.run_cmd(cmd, timeout)
        if data is None:
            return default
        return data.get(result_key, default) if result_key else data


class RulesLoading(Protocol):
    def get_candidate_tags(self) -> list: ...
    def load_detection_rules(self, matched_tags: list) -> Optional[dict]: ...


class GatewayRuleLoader:
    """Fetches principle detection rules and candidate tags from the gateway CLI."""

    def __init__(self, invoker: GatewayInvoking) -> None:
        self._invoker = invoker

    def get_candidate_tags(self) -> list:
        return self._invoker.invoke("get_candidate_tags", result_key="candidate_tags", default=[])

    def load_detection_rules(self, matched_tags: list) -> Optional[dict]:
        return self._invoker.invoke(
            "load_detection_rules",
            extra_args=["--matched_tags", ",".join(matched_tags)],
        )
