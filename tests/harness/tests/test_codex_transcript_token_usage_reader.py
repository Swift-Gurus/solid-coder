"""Tests extraction of final cumulative usage from a Codex rollout transcript."""

import tempfile
import unittest
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_HARNESS = _HERE.parent
if str(_HARNESS) not in sys.path:
    sys.path.insert(0, str(_HARNESS))

from codex_transcript_token_usage_reader import (  # noqa: E402
    CodexTranscriptTokenUsageReader,
)


"""
solid-name: TestCodexTranscriptTokenUsageReader
solid-category: unit-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Verifies comparison evidence uses the last cumulative token event and reports unavailable usage explicitly.
"""
class TestCodexTranscriptTokenUsageReader(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.transcript = Path(temporary.name) / "rollout.jsonl"
        self.sut = CodexTranscriptTokenUsageReader()

    def test_reads_last_cumulative_usage_event(self) -> None:
        self.transcript.write_text(
            '{"type":"event_msg","payload":{"type":"token_count","info":'
            '{"total_token_usage":{"input_tokens":10,"cached_input_tokens":4,'
            '"cache_write_input_tokens":0,"output_tokens":2,'
            '"reasoning_output_tokens":1,"total_tokens":12}}}}\n'
            '{"type":"event_msg","payload":{"type":"token_count","info":'
            '{"total_token_usage":{"input_tokens":30,"cached_input_tokens":20,'
            '"cache_write_input_tokens":0,"output_tokens":5,'
            '"reasoning_output_tokens":2,"total_tokens":35}}}}\n',
            encoding="utf-8",
        )

        usage = self.sut.read(self.transcript)

        self.assertTrue(usage.available)
        self.assertEqual(usage.input_tokens, 30)
        self.assertEqual(usage.cached_input_tokens, 20)
        self.assertEqual(usage.output_tokens, 5)
        self.assertEqual(usage.reasoning_output_tokens, 2)
        self.assertEqual(usage.total_tokens, 35)

    def test_reports_unavailable_when_transcript_has_no_usage_event(self) -> None:
        self.transcript.write_text(
            '{"type":"session_meta","payload":{}}\n',
            encoding="utf-8",
        )

        usage = self.sut.read(self.transcript)

        self.assertFalse(usage.available)
        self.assertEqual(usage.total_tokens, 0)


if __name__ == "__main__":
    unittest.main()
