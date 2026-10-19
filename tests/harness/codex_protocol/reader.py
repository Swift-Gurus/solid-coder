"""Reads typed workflow-call and discovery evidence from Codex transcripts."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from pydantic import TypeAdapter, ValidationError

from codex_protocol.evidence import CodexProtocolEvidence
from codex_protocol.mcp_result import CodexMcpResult
from codex_protocol.tool_call_event import CodexToolCallEvent
from codex_protocol.tool_output_event import CodexToolOutputEvent
from codex_token_usage import CodexTokenUsage
from codex_transcript_prompt_event import CodexTranscriptPromptEvent
from codex_transcript_timestamped_token_event import CodexTranscriptTimestampedTokenEvent
from review_comparison_stage_evidence import ReviewComparisonStageEvidence


"""
solid-name: CodexProtocolReader
solid-category: test-support
solid-description: Correlates workflow invocations with actual MCP responses and preserves discovery overhead and retry errors independently of scoring assertions.
"""
class CodexProtocolReader:
    def read(self, transcript: Path) -> CodexProtocolEvidence:
        decoder = TypeAdapter(Union[
            CodexToolCallEvent,
            CodexToolOutputEvent,
            CodexTranscriptPromptEvent,
            CodexTranscriptTimestampedTokenEvent,
        ])
        events = []
        for line in transcript.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                events.append(decoder.validate_json(line))
            except ValidationError:
                continue
        calls = [event for event in events if isinstance(event, CodexToolCallEvent)]
        outputs = [event for event in events if isinstance(event, CodexToolOutputEvent)]
        prompts = [event for event in events if isinstance(event, CodexTranscriptPromptEvent)]
        usage = [event for event in events if isinstance(event, CodexTranscriptTimestampedTokenEvent)]
        discovery_ids = [call.call_id for call in calls if "ALL_TOOLS" in call.input]
        starts = [call for call in calls if self._invokes(call, "flow_start")]
        nexts = [call for call in calls if self._invokes(call, "flow_next")]
        flow_call_ids = {call.call_id for call in [*starts, *nexts]}
        failures = [output for output in outputs if self._failed(output)]
        failed_ids = {output.call_id for output in failures}
        successful_ids = {
            output.call_id for output in outputs
            if output.call_id not in failed_ids
            and any(not result.is_error for result in self._mcp_results(output))
        }
        return CodexProtocolEvidence(
            transcript_path=str(transcript),
            discovery_call_ids=discovery_ids,
            discovery_output_characters=sum(
                len(text) for output in outputs if output.call_id in discovery_ids
                for text in output.texts
            ),
            startup=self._startup(prompts, starts, usage),
            flow_start_attempts=len(starts),
            flow_next_attempts=len(nexts),
            successful_flow_start_call_ids=[call.call_id for call in starts if call.call_id in successful_ids],
            successful_flow_next_call_ids=[call.call_id for call in nexts if call.call_id in successful_ids],
            failed_calls=failures,
            unanswered_call_ids=[call.call_id for call in calls if not any(output.call_id == call.call_id for output in outputs)],
            user_prompts=[event.prompt for event in prompts],
            flow_outputs=[
                text for output in outputs if output.call_id in flow_call_ids
                for text in output.texts
            ],
        )

    def _invokes(self, call: CodexToolCallEvent, tool: str) -> bool:
        return call.name in (
            f"mcp__solid-coder-flow-engine__{tool}",
            f"mcp__solid_coder_flow_engine__{tool}",
        ) or (
            call.name == "exec"
            and f"tools.mcp__solid_coder_flow_engine__{tool}(" in call.input
        )

    def _failed(self, output: CodexToolOutputEvent) -> bool:
        return any(
            text.startswith(("Script failed", "Script error:"))
            for text in output.texts
        ) or any(result.is_error for result in self._mcp_results(output))

    def _mcp_results(self, output: CodexToolOutputEvent) -> list[CodexMcpResult]:
        results = []
        for text in output.texts:
            try:
                results.append(CodexMcpResult.model_validate_json(text))
            except ValidationError:
                continue
        return results

    def _startup(
        self,
        prompts: list[CodexTranscriptPromptEvent],
        starts: list[CodexToolCallEvent],
        usage: list[CodexTranscriptTimestampedTokenEvent],
    ) -> ReviewComparisonStageEvidence | None:
        if not prompts or not starts:
            return None
        preceding_usage = [event for event in usage if event.timestamp <= starts[0].timestamp]
        return ReviewComparisonStageEvidence(
            elapsed_seconds=(starts[0].timestamp - prompts[0].timestamp).total_seconds(),
            token_usage=(
                preceding_usage[-1].token_usage
                if preceding_usage else CodexTokenUsage.unavailable()
            ),
        )
