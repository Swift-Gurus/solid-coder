"""
solid-description: Applies LLM-based correction to prompts.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional

from llm_session_running import LlmSessionRunning


class LlmPromptCorrectionService:
    """Builds the prompt via an injected builder, then runs it via an injected LlmSessionRunning."""

    def __init__(self, builder, session_runner: LlmSessionRunning) -> None:
        self._builder = builder
        self._session_runner = session_runner

    def correct(self, content: str, parent_session_id: str = "", cwd: str = "") -> Optional[str]:
        prompt = self._builder.build(content, parent_session_id)
        return self._session_runner.run(prompt, cwd=cwd)
