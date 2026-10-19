"""Separates workflow responses from explicitly requested source-file reads."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codex_protocol.evidence import CodexProtocolEvidence
from codex_protocol.reader import CodexProtocolReader


_TRANSCRIPT = '''
{"timestamp":"2026-10-19T00:00:00Z","type":"response_item","payload":{"type":"custom_tool_call","call_id":"start","name":"exec","input":"text(await tools.mcp__solid_coder_flow_engine__flow_start({flow: 'review'}))"}}
{"timestamp":"2026-10-19T00:00:01Z","type":"response_item","payload":{"type":"custom_tool_call_output","call_id":"start","output":"First workflow instruction"}}
{"timestamp":"2026-10-19T00:00:02Z","type":"response_item","payload":{"type":"custom_tool_call","call_id":"read","name":"exec","input":"text(await tools.exec_command({cmd: 'read source'}))"}}
{"timestamp":"2026-10-19T00:00:03Z","type":"response_item","payload":{"type":"custom_tool_call_output","call_id":"read","output":"REVIEWED_SOURCE"}}
{"timestamp":"2026-10-19T00:00:04Z","type":"response_item","payload":{"type":"function_call","call_id":"next","name":"mcp__solid-coder-flow-engine__flow_next","arguments":"{}"}}
{"timestamp":"2026-10-19T00:00:05Z","type":"response_item","payload":{"type":"function_call_output","call_id":"next","output":[{"text":"NEXT_RESPONSE"}]}}
'''


class TestCodexProtocolReader(TestCase):
    def read(self, next_response: str) -> CodexProtocolEvidence:
        with TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text(_TRANSCRIPT.replace("NEXT_RESPONSE", next_response))
            return CodexProtocolReader().read(transcript)

    def test_source_read_is_not_mistaken_for_workflow_source_repetition(self):
        evidence = self.read("Next workflow instruction")
        self.assertEqual(evidence.flow_outputs, [
            "First workflow instruction", "Next workflow instruction",
        ])
        self.assertNotIn("REVIEWED_SOURCE", "\n".join(evidence.flow_outputs))
        self.assertEqual(evidence.unanswered_call_ids, [])

    def test_repeated_source_in_a_workflow_response_remains_detectable(self):
        evidence = self.read("REVIEWED_SOURCE")
        self.assertEqual(evidence.flow_outputs, [
            "First workflow instruction", "REVIEWED_SOURCE",
        ])
        self.assertIn("REVIEWED_SOURCE", "\n".join(evidence.flow_outputs))
        self.assertNotIn("flow_outputs", evidence.model_dump())
