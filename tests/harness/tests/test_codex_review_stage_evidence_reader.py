"""Verifies review-stage timing and cumulative token extraction."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
if str(_HARNESS) not in sys.path:
    sys.path.insert(0, str(_HARNESS))

from codex_review_stage_evidence_reader import (  # noqa: E402
    CodexReviewStageEvidenceReader,
)


class TestCodexReviewStageEvidenceReader(unittest.TestCase):

    def test_stops_at_the_successful_review_completion_tool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text(
                "\n".join([
                    json.dumps(self._prompt_event()),
                    json.dumps(self._usage_event("2026-08-23T01:00:02Z", 10)),
                    json.dumps(self._completion_event(
                        "2026-08-23T01:00:05Z",
                        "submit_batch_findings",
                        '{"violations": []}',
                    )),
                    json.dumps(self._usage_event("2026-08-23T01:00:07Z", 30)),
                ]) + "\n",
                encoding="utf-8",
            )

            evidence = CodexReviewStageEvidenceReader().read(
                transcript=transcript,
                prompt_marker="You are a SOLID code quality gate",
                completion_tool="submit_batch_findings",
            )

        self.assertEqual(evidence.elapsed_seconds, 5)
        self.assertEqual(evidence.token_usage.total_tokens, 10)

    @staticmethod
    def _prompt_event() -> dict:
        return {
            "timestamp": "2026-08-23T01:00:00Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": "You are a SOLID code quality gate",
                }],
            },
        }

    @staticmethod
    def _usage_event(timestamp: str, total_tokens: int) -> dict:
        return {
            "timestamp": timestamp,
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {
                    "total_token_usage": {
                        "input_tokens": total_tokens - 2,
                        "cached_input_tokens": 0,
                        "cache_write_input_tokens": 0,
                        "output_tokens": 2,
                        "reasoning_output_tokens": 0,
                        "total_tokens": total_tokens,
                    }
                },
            },
        }

    @staticmethod
    def _completion_event(timestamp: str, tool: str, text: str) -> dict:
        return {
            "timestamp": timestamp,
            "type": "event_msg",
            "payload": {
                "type": "mcp_tool_call_end",
                "invocation": {"tool": tool},
                "result": {"Ok": {"content": [{"type": "text", "text": text}]}},
            },
        }


if __name__ == "__main__":
    unittest.main()
