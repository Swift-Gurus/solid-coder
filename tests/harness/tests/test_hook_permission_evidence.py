"""
solid-name: test_hook_permission_evidence
solid-category: unit-test
solid-spec: [SPEC-050]
solid-description: Verifies live hook evidence decoding against the production response encoder, including missing responses and infrastructure denials.
"""

import json

import _path_bootstrap  # noqa: F401
import pytest
from hook_decision import HookDecision
from hook_permission_evidence import HookPermissionEvidence
from hook_permission_response import HookPermissionResponse
from hook_permission_response_encoder import HookPermissionResponseEncoder
from pydantic import ValidationError


@pytest.mark.parametrize(
    "reason",
    [
        "[health-check] 1 SEVERE violation(s) found: LSP-3",
        "[health-check] Gate subprocess failed — the write is blocked.",
    ],
)
def test_retains_the_complete_production_denial_reason(reason: str) -> None:
    payload = HookPermissionResponseEncoder().encode(
        HookPermissionResponse(
            decision=HookDecision(allow=False, reason=reason),
        )
    )

    evidence = HookPermissionEvidence.model_validate_json(json.dumps(payload))

    assert evidence.event == "PreToolUse"
    assert evidence.decision == "deny"
    assert evidence.reason == reason


@pytest.mark.parametrize("payload", ["", "{}", '{"error":"hook crashed"}'])
def test_missing_hook_response_is_not_a_permission_decision(payload: str) -> None:
    with pytest.raises(ValidationError):
        HookPermissionEvidence.model_validate_json(payload)
