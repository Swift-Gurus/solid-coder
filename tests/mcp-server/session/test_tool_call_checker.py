"""Verifies explicitly injected required-tool policies and immutable defaults."""

from unittest.mock import Mock

import pytest
from session.mcp_tool_call_reader import McpToolCallReading
from session.tool_call_checker import DefaultRequiredTools, ToolCallChecker


@pytest.mark.parametrize("session_type", ["health_check", "review"])
def test_default_policy_requires_submission_before_stop(session_type: str) -> None:
    reader = Mock(spec=McpToolCallReading)
    checker = ToolCallChecker(reader=reader, required_tools=DefaultRequiredTools())
    reader.read.return_value = set()
    assert checker.check("transcript.jsonl", session_type)["allow"] is False
    reader.read.return_value = {"submit_batch_findings"}
    assert checker.check("transcript.jsonl", session_type)["allow"] is True


def test_unknown_session_type_does_not_require_transcript_reads() -> None:
    reader = Mock(spec=McpToolCallReading)
    checker = ToolCallChecker(reader=reader, required_tools=DefaultRequiredTools())
    assert checker.check("transcript.jsonl", "unmanaged") == {"allow": True}
    reader.read.assert_not_called()


def test_injected_policy_controls_required_tools() -> None:
    reader = Mock(spec=McpToolCallReading)
    policy = DefaultRequiredTools(mapping={"custom": frozenset({"custom_tool"})})
    checker = ToolCallChecker(reader=reader, required_tools=policy)
    reader.read.return_value = set()
    assert checker.check("transcript.jsonl", "custom")["allow"] is False
    reader.read.return_value = {"custom_tool"}
    assert checker.check("transcript.jsonl", "custom")["allow"] is True


def test_default_required_tools_cannot_be_mutated_through_lookup() -> None:
    provider = DefaultRequiredTools()
    with pytest.raises(AttributeError):
        provider.required_for("review").add("unrelated")
    assert provider.required_for("review") == frozenset({"submit_batch_findings"})
