"""
solid-name: test_step_renderer
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests coordinating subagent wrapping and formatting to render step results.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.step_renderer import StepRenderer
from harness.step_result import StepResult


class StubSubagentDelegator:
    def __init__(self, wrapped: str | None = None) -> None:
        self._wrapped = wrapped
        self.calls: list[tuple] = []

    def wrap_if_subagent(self, body: str, execution: dict) -> str:
        self.calls.append((body, execution))
        return self._wrapped if self._wrapped is not None else body


class StubStepFormatter:
    def __init__(self, formatted: str) -> None:
        self._formatted = formatted
        self.calls: list[tuple] = []

    def format(self, instance_id: str, body: str, rejection_reason: str | None) -> str:
        self.calls.append((instance_id, body, rejection_reason))
        return self._formatted


class TestStepRenderer(unittest.TestCase):

    def test_joins_multiple_rendered_steps_with_a_separator(self):
        formatter = StubStepFormatter("FORMATTED")
        sut = StepRenderer(subagent_delegator=StubSubagentDelegator(), step_formatter=formatter)
        steps = [
            StepResult(step_id="a", instance_id="a-1", prompt="Step A.", execution={"mode": "inline"}),
            StepResult(step_id="b", instance_id="b-1", prompt="Step B.", execution={"mode": "inline"}),
        ]

        result = sut.render_steps(steps)

        self.assertEqual(result, "FORMATTED\n\n---\n\nFORMATTED")

    def test_returns_empty_string_for_no_steps(self):
        sut = StepRenderer(subagent_delegator=StubSubagentDelegator(), step_formatter=StubStepFormatter("x"))

        self.assertEqual(sut.render_steps([]), "")

    def test_passes_the_delegators_wrapped_body_to_the_formatter(self):
        delegator = StubSubagentDelegator(wrapped="WRAPPED")
        formatter = StubStepFormatter("FORMATTED")
        sut = StepRenderer(subagent_delegator=delegator, step_formatter=formatter)
        step = StepResult(step_id="a", instance_id="a-1", prompt="Do it.", execution={"mode": "subagent"})

        sut.render_steps([step])

        self.assertEqual(delegator.calls, [("Do it.", {"mode": "subagent"})])
        self.assertEqual(formatter.calls, [("a-1", "WRAPPED", None)])

    def test_passes_the_rejection_reason_to_the_formatter(self):
        formatter = StubStepFormatter("FORMATTED")
        sut = StepRenderer(subagent_delegator=StubSubagentDelegator(), step_formatter=formatter)
        step = StepResult(
            step_id="a", instance_id="a-1", prompt="Do it.", execution={"mode": "inline"},
            rejection_reason="bad value",
        )

        sut.render_steps([step])

        self.assertEqual(formatter.calls, [("a-1", "Do it.", "bad value")])


if __name__ == "__main__":
    unittest.main()
