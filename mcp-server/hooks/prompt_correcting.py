"""
solid-description: Contract for correcting content with optional contextual parameters.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class PromptCorrecting(Protocol):
    """Builds the correction prompt, runs it through the LLM, returns corrected content or None."""

    def correct(
        self, content: str, parent_session_id: str = "", cwd: str = ""
    ) -> str | None: ...
