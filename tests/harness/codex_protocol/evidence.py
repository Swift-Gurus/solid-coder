"""Defines auditable workflow-call diagnostics separate from rule correctness."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from codex_protocol.tool_output_event import CodexToolOutputEvent
from review_comparison_stage_evidence import ReviewComparisonStageEvidence


"""
solid-name: CodexProtocolEvidence
solid-category: test-support
solid-description: Records discovery overhead, successful workflow invocations, and failed or unanswered tool calls without persisting another copy of the reviewed source.
"""
class CodexProtocolEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transcript_path: str
    discovery_call_ids: list[str]
    discovery_output_characters: int = Field(ge=0)
    startup: Optional[ReviewComparisonStageEvidence]
    flow_start_attempts: int = Field(ge=0)
    flow_next_attempts: int = Field(ge=0)
    successful_flow_start_call_ids: list[str]
    successful_flow_next_call_ids: list[str]
    failed_calls: list[CodexToolOutputEvent]
    unanswered_call_ids: list[str]
    user_prompts: list[str] = Field(default_factory=list, exclude=True)
    tool_outputs: list[str] = Field(default_factory=list, exclude=True)
