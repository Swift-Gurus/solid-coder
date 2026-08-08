"""Coordinates one prompt execution through Codex."""

from typing import Optional

from codex_command_building import CodexCommandBuilding
from codex_command_executing import CodexCommandExecuting
from codex_prompt_artifact_using import CodexPromptArtifactUsing


"""
solid-name: CodexPromptExecutor
solid-category: service
solid-description: Connects prompt artifacts, command construction, and validated execution for one response.
solid-tags: [hook, llm]
"""
class CodexPromptExecutor:
    def __init__(
        self,
        command_builder: CodexCommandBuilding,
        artifact_user: CodexPromptArtifactUsing,
        command_executor: CodexCommandExecuting,
        cwd: str = "",
    ) -> None:
        self._command_builder = command_builder
        self._artifact_user = artifact_user
        self._command_executor = command_executor
        self._cwd = cwd

    def execute(self, prompt: str, timeout: int) -> Optional[str]:
        def run_command(stdin: object, result_path) -> None:
            self._command_executor.execute(
                command=self._command_builder.build(result_path),
                timeout=timeout,
                stdin=stdin,
                cwd=self._cwd,
            )

        return self._artifact_user.use(prompt, run_command)
