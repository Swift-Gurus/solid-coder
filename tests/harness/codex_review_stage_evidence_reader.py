"""Reads review-stage timing and usage from a Codex rollout transcript."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from codex_token_usage import CodexTokenUsage
from codex_transcript_prompt_event import CodexTranscriptPromptEvent
from codex_transcript_timestamped_token_event import (
    CodexTranscriptTimestampedTokenEvent,
)
from codex_transcript_tool_completion_event import (
    CodexTranscriptToolCompletionEvent,
)
from review_comparison_stage_evidence import ReviewComparisonStageEvidence


"""
solid-name: CodexReviewStageEvidenceReader
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Measures a Codex review stage between its executed prompt and successful terminal MCP operation using cumulative transcript usage.
"""
class CodexReviewStageEvidenceReader:

    def read(
        self,
        transcript: Path,
        prompt_marker: str,
        completion_tool: str,
        completion_marker: str = "",
    ) -> ReviewComparisonStageEvidence:
        started_at: datetime | None = None
        usage = CodexTokenUsage.unavailable()
        for line in transcript.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            if started_at is None:
                started_at = self._prompt_start(line, prompt_marker)
                if started_at is None:
                    continue
            usage = self._latest_usage(line, usage)
            completed_at = self._completion(
                line,
                completion_tool,
                completion_marker,
            )
            if completed_at is not None:
                if not usage.available:
                    raise RuntimeError(
                        "Review completed before cumulative token usage was recorded"
                    )
                return ReviewComparisonStageEvidence(
                    elapsed_seconds=(completed_at - started_at).total_seconds(),
                    token_usage=usage,
                )
        raise RuntimeError("Codex transcript contains no complete review stage")

    @staticmethod
    def _prompt_start(line: str, marker: str) -> datetime | None:
        try:
            event = CodexTranscriptPromptEvent.model_validate_json(line)
        except ValidationError:
            return None
        return event.timestamp if marker in event.prompt else None

    @staticmethod
    def _latest_usage(
        line: str,
        current: CodexTokenUsage,
    ) -> CodexTokenUsage:
        try:
            event = CodexTranscriptTimestampedTokenEvent.model_validate_json(line)
        except ValidationError:
            return current
        return event.token_usage

    @staticmethod
    def _completion(
        line: str,
        tool: str,
        marker: str,
    ) -> datetime | None:
        try:
            event = CodexTranscriptToolCompletionEvent.model_validate_json(line)
        except ValidationError:
            return None
        if event.tool != tool or marker not in event.result_text:
            return None
        return event.timestamp
