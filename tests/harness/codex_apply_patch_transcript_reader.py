"""Reads apply_patch invocations from preserved Codex rollout transcripts."""

from __future__ import annotations

import json
from pathlib import Path

from codex_apply_patch_call import CodexApplyPatchCall

_PATCH_ASSIGNMENT = "const patch = "
_PATCH_INVOCATION = "tools.apply_patch("


"""
solid-name: CodexApplyPatchTranscriptReader
solid-category: test-support
solid-description: Converts direct and exec-wrapped Codex apply_patch transcript events into typed invocation observations.
"""
class CodexApplyPatchTranscriptReader:

    def read(self, sessions_root: Path) -> list[CodexApplyPatchCall]:
        calls: list[CodexApplyPatchCall] = []
        for transcript_path in sorted(sessions_root.rglob("*.jsonl")):
            calls.extend(self._read_transcript(transcript_path))
        return calls

    def _read_transcript(self, transcript_path: Path) -> list[CodexApplyPatchCall]:
        calls: list[CodexApplyPatchCall] = []
        for line in transcript_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                calls.extend(self._read_event(line, transcript_path))
        return calls

    def _read_event(
        self,
        line: str,
        transcript_path: Path,
    ) -> list[CodexApplyPatchCall]:
        event: object = json.loads(line)
        if not isinstance(event, dict) or event.get("type") != "response_item":
            return []
        payload = event.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "custom_tool_call":
            return []
        tool_name = payload.get("name")
        tool_input = payload.get("input")
        if not isinstance(tool_input, str):
            return []
        if tool_name == "apply_patch":
            return [CodexApplyPatchCall(tool_input, transcript_path)]
        if tool_name != "exec":
            return []
        invocation_count = tool_input.count(_PATCH_INVOCATION)
        if invocation_count == 0:
            return []
        patch_content = self._read_assigned_patch(tool_input)
        return [
            CodexApplyPatchCall(patch_content, transcript_path)
            for _invocation in range(invocation_count)
        ]

    def _read_assigned_patch(self, tool_input: str) -> str:
        assignment_offset = tool_input.find(_PATCH_ASSIGNMENT)
        if assignment_offset < 0:
            raise RuntimeError("Codex exec invoked apply_patch without a patch assignment")
        encoded_patch = tool_input[assignment_offset + len(_PATCH_ASSIGNMENT):]
        patch_content, _end_offset = json.JSONDecoder().raw_decode(encoded_patch)
        if not isinstance(patch_content, str):
            raise RuntimeError("Codex apply_patch assignment was not a string")
        return patch_content
