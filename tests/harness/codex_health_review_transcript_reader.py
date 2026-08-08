"""Reads isolated health-review submissions from Codex rollout transcripts."""

from __future__ import annotations

import json
from pathlib import Path

from codex_health_review_submission import CodexHealthReviewSubmission


"""
solid-name: CodexHealthReviewTranscriptReader
solid-category: test-support
solid-description: Converts submit_batch_findings completion events into typed per-file health-review observations.
"""
class CodexHealthReviewTranscriptReader:

    def read(self, sessions_root: Path) -> list[CodexHealthReviewSubmission]:
        submissions: list[CodexHealthReviewSubmission] = []
        for transcript_path in sorted(sessions_root.rglob("*.jsonl")):
            submissions.extend(self._read_transcript(transcript_path))
        return submissions

    def _read_transcript(
        self,
        transcript_path: Path,
    ) -> list[CodexHealthReviewSubmission]:
        submissions: list[CodexHealthReviewSubmission] = []
        for line in transcript_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            submission = self._read_event(line, transcript_path)
            if submission is not None:
                submissions.append(submission)
        return submissions

    def _read_event(
        self,
        line: str,
        transcript_path: Path,
    ) -> CodexHealthReviewSubmission | None:
        event: object = json.loads(line)
        if not isinstance(event, dict) or event.get("type") != "event_msg":
            return None
        payload = event.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "mcp_tool_call_end":
            return None
        invocation = payload.get("invocation")
        if not isinstance(invocation, dict) or invocation.get("tool") != "submit_batch_findings":
            return None
        arguments = invocation.get("arguments")
        if not isinstance(arguments, dict):
            raise RuntimeError("submit_batch_findings event had no arguments")
        principle_payloads = arguments.get("submissions")
        if not isinstance(principle_payloads, dict):
            raise RuntimeError("submit_batch_findings event had no submissions")
        file_names = self._file_names(principle_payloads)
        if len(file_names) != 1:
            raise RuntimeError(
                "Expected one reviewed file per health session; "
                f"observed {sorted(file_names)}"
            )
        return CodexHealthReviewSubmission(
            file_name=next(iter(file_names)),
            principle_names=frozenset(str(name) for name in principle_payloads),
            transcript_path=transcript_path,
            successful=self._submission_succeeded(payload),
        )

    def _submission_succeeded(self, payload: dict) -> bool:
        result = payload.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("submit_batch_findings event had no result")
        successful_result = result.get("Ok")
        if not isinstance(successful_result, dict):
            return False
        content = successful_result.get("content")
        if not isinstance(content, list):
            raise RuntimeError("submit_batch_findings result had no content")
        for content_item in content:
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if not isinstance(text, str):
                continue
            response_start = text.find("{")
            if response_start < 0:
                continue
            response: object = json.loads(text[response_start:])
            if not isinstance(response, dict):
                continue
            if "violations" in response:
                return True
            if "error" in response:
                return False
        raise RuntimeError("submit_batch_findings result had no recognized response")

    def _file_names(self, principle_payloads: dict) -> set[str]:
        file_names: set[str] = set()
        for principle_payload in principle_payloads.values():
            if not isinstance(principle_payload, dict):
                continue
            files = principle_payload.get("files")
            if not isinstance(files, list):
                continue
            for reviewed_file in files:
                if not isinstance(reviewed_file, dict):
                    continue
                file_path = reviewed_file.get("file_path")
                if isinstance(file_path, str):
                    file_names.add(Path(file_path).name)
        return file_names
