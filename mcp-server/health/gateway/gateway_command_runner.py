"""Runs health-check gateway commands through the shared JSON subprocess contract."""

import sys
from pathlib import Path
from typing import Optional, Protocol

from hook_utils import SubprocessJsonRunning, _default_subprocess_runner


"""
solid-name: GatewayInvoking
solid-category: abstraction
solid-description: Contract for invoking gateway operations and selecting response fields.
"""
class GatewayInvoking(Protocol):
    def invoke(
        self,
        subcommand: str,
        extra_args: Optional[list] = None,
        result_key: Optional[str] = None,
        default=None,
    ): ...


"""
solid-name: GatewayCommandRunner
solid-category: service
solid-description: Executes gateway health-check commands with timeout handling and parsed responses.
"""
class GatewayCommandRunner:
    def __init__(
        self,
        gateway: Path,
        timeout: int,
        runner: SubprocessJsonRunning = _default_subprocess_runner,
        executable: str = sys.executable,
    ) -> None:
        self._gateway = gateway
        self._timeout = timeout
        self._runner = runner
        self._executable = executable

    def invoke(
        self,
        subcommand: str,
        extra_args: Optional[list] = None,
        result_key: Optional[str] = None,
        default=None,
    ):
        command = [self._executable, str(self._gateway), subcommand] + (extra_args or [])
        data = self._runner.run(command, timeout=self._timeout)
        if data is None:
            return default
        return data.get(result_key, default) if result_key else data
