"""Reads cumulative usage from Codex rollout transcripts."""

from pathlib import Path

from pydantic import ValidationError

from codex_token_usage import CodexTokenUsage
from codex_transcript_token_event import CodexTranscriptTokenEvent


"""
solid-name: CodexTranscriptTokenUsageReader
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Returns the final cumulative token event from a preserved rollout while making absent usage explicit.
"""
class CodexTranscriptTokenUsageReader:
    def read(self, transcript: Path) -> CodexTokenUsage:
        latest = CodexTokenUsage.unavailable()
        for line in transcript.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = CodexTranscriptTokenEvent.model_validate_json(line)
            except ValidationError:
                continue
            if event.event_type == "token_count" and event.total_usage is not None:
                latest = event.total_usage
        return latest
