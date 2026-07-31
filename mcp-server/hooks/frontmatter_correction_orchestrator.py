"""
solid-description: Applies content correction and updates tool input when changes occur.
solid-category: service
solid-tags: [hook]
"""

from prompt_correcting import PromptCorrecting
from hook_utils import HookResponder
from tool_content_extractor import ToolContentExtractor


class FrontmatterCorrectionOrchestrator:
    """Runs the injected PromptCorrecting, then issues allow (optionally with an updated tool input)."""

    def __init__(self, correction_service: PromptCorrecting, content_extractor: ToolContentExtractor) -> None:
        self._service = correction_service
        self._content_extractor = content_extractor

    def correct(
        self,
        tool_name: str,
        tool_input: dict,
        content: str,
        session_id: str,
        cwd: str,
        responder: HookResponder,
    ) -> None:
        corrected = self._service.correct(content, parent_session_id=session_id, cwd=cwd)
        if corrected is None or corrected == content:
            responder.allow()
            return
        updated = dict(tool_input)
        updated[self._content_extractor.input_key_for(tool_name)] = corrected
        responder.allow(updated_input=updated)