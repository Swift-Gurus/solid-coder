"""
solid-description: Runs LLM inference with prompts and returns results.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from codex_command_builder import CodexCommandBuilder  # noqa: E402
from codex_profile_manager import CodexProfileManager  # noqa: E402
from codex_temp_file_manager import CodexTempFileManager  # noqa: E402
from hook_utils import SubprocessError, SubprocessRunning, SubprocessAdapter  # noqa: E402


class CommandBuilding(Protocol):
    def build(self, result_path: Path) -> list: ...


class TempFileManaging(Protocol):
    def write_prompt(self, prompt: str) -> Path: ...
    def result_path(self) -> Path: ...
    def prompt_stdin(self, path: Path): ...
    def read_result(self, path: Path) -> Optional[str]: ...
    def cleanup(self, *paths: Path) -> None: ...


class CodexRunner:
    """Facade: all stored properties are protocol-typed; run() is pure delegation."""

    def __init__(
        self,
        cmd_builder: CommandBuilding,
        temp_files: TempFileManaging,
        subprocess_runner: SubprocessRunning,
    ) -> None:
        self._cmd_builder = cmd_builder
        self._temp_files = temp_files
        self._runner = subprocess_runner

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        result_path = self._temp_files.result_path()
        prompt_path = self._temp_files.write_prompt(prompt)
        try:
            cmd = self._cmd_builder.build(result_path)
            with self._temp_files.prompt_stdin(prompt_path) as pf:
                ok, stdout, stderr = self._runner.run(cmd, timeout=timeout, stdin=pf)
            if not ok:
                detail = stderr[:300] or stdout[:300]
                raise SubprocessError(f"`codex exec` exited with error: {detail}")
            return self._temp_files.read_result(result_path)
        finally:
            self._temp_files.cleanup(result_path, prompt_path)


def make_codex_runner(
    model: str = "",
    timeout: int = 300,
    codex_home: str = "",
) -> CodexRunner:
    """Return a CodexRunner with the health-check profile written to the user's CODEX_HOME."""
    profile_name = CodexProfileManager(codex_home=codex_home).ensure_profile()
    return CodexRunner(
        cmd_builder=CodexCommandBuilder(model=model, profile_name=profile_name),
        temp_files=CodexTempFileManager(),
        subprocess_runner=SubprocessAdapter(),
    )
