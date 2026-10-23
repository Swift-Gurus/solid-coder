"""Tests nonterminal warnings survive permission and input-update responses."""

import sys
from importlib import import_module
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))

import_module("_path_bootstrap")
from decision_capturing_gate import DecisionCapturingGate
from hook_context_buffer import HookContextBuffer
from hook_gate import HookGate
from hook_responder import HookResponder
from review_decision_store import ReviewDecisionStore


def test_captured_warning_survives_allow_and_does_not_override_denial():
    gate = DecisionCapturingGate(Mock(), ReviewDecisionStore(HookContextBuffer()))

    gate.warn("Evidence is unavailable for a verified new interface.")
    gate.block("Known SEVERE finding")
    gate.allow()

    assert gate.decision.allow is False
    assert gate.decision.reason == "Known SEVERE finding"
    assert "verified new interface" in gate.decision.additional_context
    assert gate.decision.additional_context.count("verified new interface") == 1


def test_warning_does_not_emit_permission_before_final_allow():
    responder = Mock()
    gate = HookGate(Mock(), responder, HookContextBuffer())

    gate.warn("Review evidence warning")

    responder.allow.assert_not_called()
    responder.block.assert_not_called()
    gate.allow("Other context", updated_input={"content": "corrected"})
    responder.allow.assert_called_once_with(
        "Review evidence warning\n\nOther context", {"content": "corrected"}
    )
    gate.allow()
    assert responder.allow.call_args.args == ("", None)


def test_warning_also_survives_a_block_response():
    responder = Mock()
    gate = HookGate(Mock(), responder, HookContextBuffer())

    gate.warn("Unverified evidence")
    gate.block("Severe finding")

    responder.block.assert_called_once_with("Severe finding", "Unverified evidence")


def test_hook_response_preserves_warning_alongside_corrected_input():
    output = Mock()
    responder = HookResponder(output=output, process=Mock())

    responder.allow(
        additional_context="Warning", updated_input={"content": "corrected"}
    )

    response = output.write_result.call_args.args[0]["hookSpecificOutput"]
    assert response["permissionDecision"] == "allow"
    assert response["updatedInput"] == {"content": "corrected"}
    assert response["additionalContext"] == "Warning"
