"""Verifies workflow invocation correctness independently of tool discovery."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HARNESS))

import test_srp_validation_live
from codex_protocol.evidence import CodexProtocolEvidence
from live_session_result import LiveSessionResult
from preserved_live_workflow_run import PreservedLiveWorkflowRun

"""
solid-name: TestCodexRuleProtocol
solid-category: unit-test
solid-description: Verifies discovered workflow tools and recovered submission errors remain auditable without weakening successful invocation requirements.
"""


class TestCodexRuleProtocol(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sessions = self.root / "codex-runtime" / "sessions"
        self.sessions.mkdir(parents=True)
        self.case = test_srp_validation_live.TestCodexSRPValidationLive()
        self.run = PreservedLiveWorkflowRun(
            session=LiveSessionResult("child", "done", self.root),
            run_directory=self.root / "flow-run",
        )

    def test_discovery_before_successful_workflow_calls_is_recorded_not_rejected(
        self,
    ) -> None:
        self._write_transcript(
            self._call(
                "discover", "text(ALL_TOOLS.filter(t => t.name.includes('flow')));"
            ),
            self._output(
                "discover", "Registered flow_start and flow_next", as_blocks=True
            ),
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output(
                "start", '{"content":[{"type":"text","text":"ready"}]}', as_blocks=True
            ),
            self._call(
                "next",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}});",
            ),
            self._output("next", '{"content":[{"type":"text","text":"done"}]}'),
        )

        self.case._assert_codex_protocol(self.run)
        evidence = CodexProtocolEvidence.model_validate_json(
            (self.root / "codex-protocol-evidence.json").read_text()
        )

        self.assertEqual(evidence.discovery_call_ids, ["discover"])
        self.assertEqual(evidence.discovery_output_characters, 35)
        self.assertEqual(evidence.startup.elapsed_seconds, 1)
        self.assertEqual(evidence.successful_flow_next_call_ids, ["next"])

    def test_recovered_script_error_remains_in_saved_evidence(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output("start", '{"content":[{"type":"text","text":"ready"}]}'),
            self._call(
                "broken",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}}));",
            ),
            self._output(
                "broken",
                "Script failed\nScript error:\nSyntaxError: Unexpected token ')'",
            ),
            self._call(
                "retry",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}});",
            ),
            self._output("retry", '{"content":[{"type":"text","text":"done"}]}'),
        )

        self.case._assert_codex_protocol(self.run)
        evidence = CodexProtocolEvidence.model_validate_json(
            (self.root / "codex-protocol-evidence.json").read_text()
        )

        self.assertEqual(evidence.flow_next_attempts, 2)
        self.assertEqual(evidence.successful_flow_next_call_ids, ["retry"])
        self.assertEqual([event.call_id for event in evidence.failed_calls], ["broken"])
        self.assertIn("SyntaxError", evidence.failed_calls[0].texts[0])

    def test_failed_start_is_not_a_successful_invocation(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output(
                "start", "Script failed\nTypeError: flow_start is not a function"
            ),
        )

        with self.assertRaisesRegex(AssertionError, "successful flow_start"):
            self.case._assert_codex_protocol(self.run)

        self.assertIn(
            "not a function", (self.root / "codex-protocol-evidence.json").read_text()
        )

    def test_missing_next_is_not_a_completed_protocol(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output("start", '{"content":[{"type":"text","text":"ready"}]}'),
        )

        with self.assertRaisesRegex(AssertionError, "successful flow_next"):
            self.case._assert_codex_protocol(self.run)

    def test_missing_codex_transcript_fails_instead_of_skipping_validation(
        self,
    ) -> None:
        with self.assertRaisesRegex(AssertionError, "Codex transcript"):
            self.case._assert_codex_protocol(self.run)

    def test_mcp_error_response_cannot_satisfy_successful_start(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output(
                "start",
                '{"content":[{"type":"text","text":"unknown flow"}],"isError":true}',
            ),
        )

        with self.assertRaisesRegex(AssertionError, "successful flow_start"):
            self.case._assert_codex_protocol(self.run)

    def test_response_for_another_call_cannot_satisfy_start(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output("unrelated", '{"content":[{"type":"text","text":"ready"}]}'),
        )

        with self.assertRaisesRegex(AssertionError, "successful flow_start"):
            self.case._assert_codex_protocol(self.run)

    def test_workflow_failure_still_fails_after_successful_tool_calls(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output("start", '{"content":[{"type":"text","text":"ready"}]}'),
            self._call(
                "next",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}});",
            ),
            self._output("next", '{"content":[{"type":"text","text":"failed"}]}'),
        )
        self.run.run_directory.mkdir()
        (self.run.run_directory / "events.jsonl").write_text('{"event":"run_failed"}\n')

        with self.assertRaisesRegex(AssertionError, "run_completed"):
            self.case.assert_workflow(self.run)

        self.assertTrue((self.root / "codex-protocol-evidence.json").is_file())

    def test_startup_usage_is_separate_from_later_review_usage(self) -> None:
        self._write_transcript(
            '{"timestamp":"2026-10-02T00:00:00.5Z","type":"event_msg",'
            '"payload":{"type":"token_count","info":{"total_token_usage":'
            '{"input_tokens":100,"cached_input_tokens":50,"cache_write_input_tokens":0,'
            '"output_tokens":10,"reasoning_output_tokens":0,"total_tokens":110}}}}',
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output("start", '{"content":[{"type":"text","text":"ready"}]}'),
            self._call(
                "next",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}});",
            ),
            self._output("next", '{"content":[{"type":"text","text":"done"}]}'),
            '{"timestamp":"2026-10-02T00:00:03Z","type":"event_msg",'
            '"payload":{"type":"token_count","info":{"total_token_usage":'
            '{"input_tokens":200,"cached_input_tokens":100,"cache_write_input_tokens":0,'
            '"output_tokens":20,"reasoning_output_tokens":0,"total_tokens":220}}}}',
        )

        self.case._assert_codex_protocol(self.run)
        evidence = CodexProtocolEvidence.model_validate_json(
            (self.root / "codex-protocol-evidence.json").read_text()
        )

        self.assertEqual(evidence.startup.token_usage.total_tokens, 110)
        self.assertNotIn(self.case.FIXTURE.read_text(), evidence.model_dump_json())

    def test_unwrapped_responses_require_completed_server_evidence_for_the_same_session(
        self,
    ) -> None:
        self._write_transcript(
            self._call(
                "start",
                "const r = await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'}); text(r.content[0].text);",
            ),
            self._output("start", "Classify the supplied unit.", as_blocks=True),
            self._call(
                "next",
                "const r = await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}}); text(r.content[0].text);",
            ),
            self._output("next", "Flow complete.", as_blocks=True),
        )
        self.run.run_directory.mkdir()
        events = self.run.run_directory / "events.jsonl"
        for session in ["unrelated", "child"]:
            events.write_text(
                "\n".join(
                    [
                        '{"event":"run_started"}',
                        json.dumps(
                            {"event": "session_step_recorded", "session_id": session}
                        ),
                        '{"event":"run_completed"}',
                    ]
                )
            )
            if session == "unrelated":
                with self.assertRaisesRegex(AssertionError, "successful flow_start"):
                    self.case._assert_codex_protocol(self.run)
            else:
                self.case._assert_codex_protocol(self.run)

    def test_plain_completion_text_alone_does_not_prove_workflow_success(self) -> None:
        self._write_transcript(
            self._call(
                "start",
                "await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'});",
            ),
            self._output("start", "Flow complete."),
            self._call(
                "next",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}});",
            ),
            self._output("next", "Flow complete."),
        )

        with self.assertRaisesRegex(AssertionError, "successful flow_start"):
            self.case._assert_codex_protocol(self.run)

    def test_recovered_error_with_unwrapped_responses_preserves_completed_server_evidence(
        self,
    ) -> None:
        self._write_transcript(
            self._call(
                "start",
                "const r = await tools.mcp__solid_coder_flow_engine__flow_start({flow:'srp'}); text(r.content[0].text);",
            ),
            self._output("start", "Classify the supplied unit.", as_blocks=True),
            self._call(
                "broken",
                "await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}}));",
            ),
            self._output(
                "broken",
                "Script failed\nScript error:\nSyntaxError: Unexpected token ')'",
            ),
            self._call(
                "retry",
                "const r = await tools.mcp__solid_coder_flow_engine__flow_next({outputs:{}}); text(r.content[0].text);",
            ),
            self._output("retry", "Flow complete.", as_blocks=True),
        )
        self.run.run_directory.mkdir()
        (self.run.run_directory / "events.jsonl").write_text(
            '{"event":"run_started"}\n{"event":"session_step_recorded","session_id":"child"}\n{"event":"run_completed"}'
        )

        self.case._assert_codex_protocol(self.run)

        evidence = CodexProtocolEvidence.model_validate_json(
            (self.root / "codex-protocol-evidence.json").read_text()
        )
        self.assertEqual([event.call_id for event in evidence.failed_calls], ["broken"])
        self.assertIn("SyntaxError", evidence.failed_calls[0].texts[0])

    def _write_transcript(self, *events: str) -> None:
        source = json.dumps(self.case.FIXTURE.read_text())
        prompt = (
            '{"timestamp":"2026-10-02T00:00:00Z","type":"response_item",'
            '"payload":{"type":"message","role":"user",'
            f'"content":[{{"type":"input_text","text":{source}}}]}}}}'
        )
        (self.sessions / "rollout.jsonl").write_text("\n".join([prompt, *events]))

    def _call(self, call_id: str, code: str) -> str:
        return (
            '{"timestamp":"2026-10-02T00:00:01Z","type":"response_item",'
            '"payload":{"type":"custom_tool_call","name":"exec",'
            f'"call_id":{json.dumps(call_id)},"input":{json.dumps(code)}}}}}'
        )

    def _output(self, call_id: str, output: str, as_blocks: bool = False) -> str:
        encoded = json.dumps(output)
        content = (
            f'[{{"type":"input_text","text":{encoded}}}]' if as_blocks else encoded
        )
        return (
            '{"timestamp":"2026-10-02T00:00:02Z","type":"response_item",'
            '"payload":{"type":"custom_tool_call_output",'
            f'"call_id":{json.dumps(call_id)},"output":{content}}}}}'
        )
