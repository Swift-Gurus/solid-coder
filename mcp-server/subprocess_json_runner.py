"""
solid-name: SubprocessJsonRunner
solid-category: service
solid-description: Executes commands and returns their results as parsed objects with consistent error handling.
"""

import json
from typing import Optional

from hook_utils import SubprocessError, SubprocessRunning


class SubprocessJsonRunner:
    """Runs a subprocess command and parses stdout as JSON.

    Reuses SubprocessRunning for execution; adds JSON parsing and error raising.
    """

    def __init__(self, runner: SubprocessRunning) -> None:
        self._runner = runner

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> object:
        runner_kwargs: dict = {"timeout": timeout, "stdin": stdin}
        if cwd is not None:
            runner_kwargs["cwd"] = cwd
        try:
            success, stdout, stderr = self._runner.run(cmd, **runner_kwargs)
        except SubprocessError:
            raise
        except Exception as exc:
            raise SubprocessError(f"`{cmd[0]}` failed: {exc}")
        if not success:
            label = " ".join(cmd[:2])
            raise SubprocessError(
                f"`{label}` exited with error" + (f":\n{stderr}" if stderr else "")
            )
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise SubprocessError(f"`{cmd[0]}` produced invalid JSON: {exc}")
