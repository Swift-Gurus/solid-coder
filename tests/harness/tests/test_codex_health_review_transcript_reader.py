"""Verifies health-review extraction from Codex rollout transcripts."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from codex_health_review_transcript_reader import (  # noqa: E402
    CodexHealthReviewTranscriptReader,
)
from codex_health_review_submission import CodexHealthReviewSubmission  # noqa: E402


class TestCodexHealthReviewTranscriptReader(unittest.TestCase):

    def test_reads_one_file_and_all_submitted_principles(self) -> None:
        submissions = {
            "dry": self._principle_payload("DashboardView.swift"),
            "srp": self._principle_payload("DashboardView.swift"),
        }

        observed = self._read(submissions)

        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0].file_name, "DashboardView.swift")
        self.assertEqual(observed[0].principle_names, frozenset({"dry", "srp"}))
        self.assertTrue(observed[0].successful)

    def test_preserves_rejected_attempts_before_successful_retry(self) -> None:
        submissions = {
            "dry": self._principle_payload("InventoryView.swift"),
            "srp": self._principle_payload("InventoryView.swift"),
        }

        observed = self._read_attempts(submissions, [False, False, True])

        self.assertEqual(
            [submission.successful for submission in observed],
            [False, False, True],
        )
        self.assertEqual(
            {submission.transcript_path for submission in observed},
            {observed[0].transcript_path},
        )

    def test_rejects_multiple_files_in_one_health_submission(self) -> None:
        submissions = {
            "dry": {
                "files": [
                    {"file_path": "/workspace/One.swift"},
                    {"file_path": "/workspace/Two.swift"},
                ]
            }
        }

        with self.assertRaisesRegex(RuntimeError, "one reviewed file"):
            self._read(submissions)

    def _principle_payload(self, file_name: str) -> dict:
        return {"files": [{"file_path": f"/workspace/{file_name}"}]}

    def _read(self, submissions: dict) -> list[CodexHealthReviewSubmission]:
        return self._read_attempts(submissions, [True])

    def _read_attempts(
        self,
        submissions: dict,
        successful_attempts: list[bool],
    ) -> list[CodexHealthReviewSubmission]:
        with tempfile.TemporaryDirectory() as directory:
            sessions_root = Path(directory)
            transcript = sessions_root / "rollout.jsonl"
            transcript.write_text(
                "\n".join(
                    json.dumps(self._event(submissions, successful))
                    for successful in successful_attempts
                ),
                encoding="utf-8",
            )
            return CodexHealthReviewTranscriptReader().read(sessions_root)

    def _event(self, submissions: dict, successful: bool) -> dict:
        response = {"violations": []} if successful else {"error": "invalid metrics"}
        return {
            "type": "event_msg",
            "payload": {
                "type": "mcp_tool_call_end",
                "invocation": {
                    "tool": "submit_batch_findings",
                    "arguments": {"submissions": submissions},
                },
                "result": {
                    "Ok": {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Show this output exactly as-is:\n\n"
                                    + json.dumps(response)
                                ),
                            }
                        ]
                    }
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
