"""
solid-name: test_session_validation_handler
solid-category: unit-test
solid-description: Validates applicability filtering and validation decision-making for session events.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stop_handler_doubles import StubValidateFn
from session_validation_handler import (
    SessionStopApplicabilityChecker,
    SessionStopValidator,
    SessionValidationHandler,
)


class TestSessionStopApplicabilityChecker(unittest.TestCase):
    def setUp(self):
        self.checker = SessionStopApplicabilityChecker()

    def test_does_not_apply_when_stop_hook_already_active(self):
        self.assertFalse(self.checker.applies({"stop_hook_active": True, "session_id": "abc"}))

    def test_does_not_apply_without_session_id(self):
        self.assertFalse(self.checker.applies({}))

    def test_applies_with_session_id_and_not_reentrant(self):
        self.assertTrue(self.checker.applies({"session_id": "abc"}))


class TestSessionStopValidator(unittest.TestCase):
    def test_allow_result_produces_allow_decision(self):
        validator = SessionStopValidator(validate_fn=StubValidateFn({"allow": True}))

        decision = validator.validate({"session_id": "abc", "transcript_path": "t", "cwd": "/tmp"})

        self.assertTrue(decision.allow)

    def test_deny_result_carries_reason_through(self):
        validator = SessionStopValidator(validate_fn=StubValidateFn({"allow": False, "reason": "missing tool call"}))

        decision = validator.validate({"session_id": "abc"})

        self.assertFalse(decision.allow)
        self.assertEqual(decision.reason, "missing tool call")

    def test_deny_without_explicit_reason_falls_back_to_default(self):
        validator = SessionStopValidator(validate_fn=StubValidateFn({"allow": False}))

        decision = validator.validate({"session_id": "abc"})

        self.assertEqual(decision.reason, "Required MCP tools were not called.")

    def test_missing_cwd_falls_back_to_injected_cwd_provider(self):
        validate_fn = StubValidateFn({"allow": True})
        validator = SessionStopValidator(validate_fn=validate_fn, cwd_provider=lambda: "/injected/cwd")

        validator.validate({"session_id": "abc"})

        self.assertEqual(validate_fn.calls[0][2], "/injected/cwd")

    def test_event_cwd_takes_precedence_over_provider(self):
        validate_fn = StubValidateFn({"allow": True})
        validator = SessionStopValidator(validate_fn=validate_fn, cwd_provider=lambda: "/should/not/be/used")

        validator.validate({"session_id": "abc", "cwd": "/event/cwd"})

        self.assertEqual(validate_fn.calls[0][2], "/event/cwd")


class TestSessionValidationHandler(unittest.TestCase):
    def test_should_handle_delegates_to_applicability_checker(self):
        handler = SessionValidationHandler(applicability=SessionStopApplicabilityChecker())

        self.assertFalse(handler.should_handle({}))
        self.assertTrue(handler.should_handle({"session_id": "abc"}))

    def test_handle_delegates_to_validator(self):
        validator = SessionStopValidator(validate_fn=StubValidateFn({"allow": False, "reason": "nope"}))
        handler = SessionValidationHandler(validator=validator)

        decision = handler.handle({"session_id": "abc"})

        self.assertFalse(decision.allow)
        self.assertEqual(decision.reason, "nope")


if __name__ == "__main__":
    unittest.main()
