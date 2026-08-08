"""
solid-description: Manages execution of external commands with file-based input and result handling.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from codex_command_executor import CodexCommandExecutor  # noqa: E402
from codex_command_builder import CodexCommandBuilder  # noqa: E402
from codex_execution_validator import CodexExecutionValidator  # noqa: E402
from codex_mcp_config_argument_builder import CodexMcpConfigArgumentBuilder  # noqa: E402
from codex_prompt_artifact_user import CodexPromptArtifactUser  # noqa: E402
from codex_prompt_executing import CodexPromptExecuting  # noqa: E402
from codex_prompt_executor import CodexPromptExecutor  # noqa: E402
from codex_temp_file_manager import CodexTempFileManager  # noqa: E402
from hook_utils import SubprocessAdapter  # noqa: E402
from llama.json_deserializer import JsonDeserializer  # noqa: E402
from llama.json_serializer import JsonSerializer  # noqa: E402
from subprocess_error_factory import SubprocessErrorFactory  # noqa: E402


"""
solid-name: CodexRunner
solid-category: service
solid-description: Delegates prompt execution to a configured Codex execution service.
"""
class CodexRunner:
    """Facade: all stored properties are protocol-typed; run() is pure delegation."""

    def __init__(
        self,
        prompt_executor: CodexPromptExecuting,
    ) -> None:
        self._prompt_executor = prompt_executor

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        return self._prompt_executor.execute(prompt, timeout)


def make_codex_runner(
    model: str = "",
    timeout: int = 300,
    cwd: str = "",
    mcp_config: str = "",
) -> CodexRunner:
    """Return a CodexRunner configured with isolated inline health-session servers."""
    temp_files = CodexTempFileManager()
    return CodexRunner(
        prompt_executor=CodexPromptExecutor(
            command_builder=CodexCommandBuilder(
                model=model,
                mcp_config=mcp_config,
                config_argument_builder=CodexMcpConfigArgumentBuilder(
                    deserializer=JsonDeserializer(),
                    serializer=JsonSerializer(),
                ),
            ),
            artifact_user=CodexPromptArtifactUser(prompt_session=temp_files),
            command_executor=CodexCommandExecutor(
                subprocess_runner=SubprocessAdapter(),
                execution_validator=CodexExecutionValidator(
                    error_factory=SubprocessErrorFactory(),
                ),
            ),
            cwd=cwd,
        ),
    )
