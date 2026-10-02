"""Defines a textual fragment in a Codex tool response."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: CodexOutputText
solid-category: test-support
solid-description: Carries the text of a tool-result content block for transcript diagnostics.
"""
class CodexOutputText(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    text: str
