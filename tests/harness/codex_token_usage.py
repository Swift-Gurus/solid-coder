"""Defines cumulative token evidence from one Codex session."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: CodexTokenUsage
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Carries explicit availability and cumulative token counters preserved for one comparison run.
"""
class CodexTokenUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    available: bool = True
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int

    @classmethod
    def unavailable(cls) -> "CodexTokenUsage":
        return cls(
            available=False,
            input_tokens=0,
            cached_input_tokens=0,
            cache_write_input_tokens=0,
            output_tokens=0,
            reasoning_output_tokens=0,
            total_tokens=0,
        )
