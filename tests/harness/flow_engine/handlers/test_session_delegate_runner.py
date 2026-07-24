"""
solid-name: test_session_delegate_runner
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests spawning an LLM session for a delegate step's isolated flow and mapping its result to a step run outcome.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.session_delegate_runner import SessionDelegateRunner


class StubRunner:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def run(self, prompt: str, timeout: int):
        self.calls.append((prompt, timeout))
        return self._result


class TestSessionDelegateRunner(unittest.TestCase):

    def test_builds_config_from_plugin_root_and_reports_success_outcome(self):
        runner = StubRunner("delegate complete")
        factory_calls: list[dict] = []

        def runner_factory(**kwargs):
            factory_calls.append(kwargs)
            return runner

        sut = SessionDelegateRunner(
            plugin_root=Path("/plugin"),
            timeout=120,
            cwd_resolver=lambda: Path("/project"),
            runner_factory=runner_factory,
            mcp_config_builder=lambda root: f"config-for:{root}",
        )

        outcome = sut.run("Call flow_start with flow=\"x\" and isolated=true.")

        self.assertFalse(outcome.awaiting_input)
        self.assertIsNone(outcome.rejection_reason)
        self.assertEqual(outcome.outputs, {})
        self.assertEqual(factory_calls, [{
            "mcp_config": "config-for:/plugin",
            "allowed_tools": "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status",
            "cwd": "/project",
        }])
        self.assertEqual(runner.calls, [("Call flow_start with flow=\"x\" and isolated=true.", 120)])

    def test_reports_rejection_when_runner_returns_none(self):
        sut = SessionDelegateRunner(
            plugin_root=Path("/plugin"),
            timeout=60,
            cwd_resolver=lambda: Path("/project"),
            runner_factory=lambda **kwargs: StubRunner(None),
            mcp_config_builder=lambda root: "config",
        )

        outcome = sut.run("prompt")

        self.assertFalse(outcome.awaiting_input)
        self.assertIsNotNone(outcome.rejection_reason)
        self.assertIsNone(outcome.outputs)


if __name__ == "__main__":
    unittest.main()
