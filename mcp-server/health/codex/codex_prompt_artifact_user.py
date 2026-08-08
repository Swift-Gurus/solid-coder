"""Runs operations with managed prompt execution artifacts."""

from pathlib import Path
from typing import Callable, Optional

from codex_prompt_session_managing import CodexPromptSessionManaging


"""
solid-name: CodexPromptArtifactUser
solid-category: service
solid-description: Manages prompt artifact allocation, access, result retrieval, and cleanup for one operation.
solid-tags: [hook, llm]
"""
class CodexPromptArtifactUser:
    def __init__(self, prompt_session: CodexPromptSessionManaging) -> None:
        self._prompt_session = prompt_session

    def use(
        self,
        prompt: str,
        operation: Callable[[object, Path], None],
    ) -> Optional[str]:
        result_path = self._prompt_session.result_path()
        prompt_path = self._prompt_session.write_prompt(prompt)
        try:
            with self._prompt_session.prompt_stdin(prompt_path) as prompt_input:
                operation(prompt_input, result_path)
            return self._prompt_session.read_result(result_path)
        finally:
            self._prompt_session.cleanup(result_path, prompt_path)
