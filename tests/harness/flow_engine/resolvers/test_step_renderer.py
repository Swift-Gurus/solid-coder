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

from harness.batch_step_renderer_factory import BatchStepRendererFactory
from harness.first_ready_step_selector import FirstReadyStepSelector
from harness.sibling_batch_step_selector_factory import (
    SiblingBatchStepSelectorFactory,
)
from harness.single_step_renderer import SingleStepRenderer
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

    def test_renders_only_the_first_ready_step(self):
        formatter = StubStepFormatter("FORMATTED")
        sut = self._renderer(StubSubagentDelegator(), formatter)
        steps = [
            StepResult(step_id="a", instance_id="a-1", prompt="Step A.", execution={"mode": "inline"}),
            StepResult(step_id="b", instance_id="b-1", prompt="Step B.", execution={"mode": "inline"}),
        ]

        result = sut.render_steps(steps)

        self.assertEqual(result, "FORMATTED")
        self.assertEqual(formatter.calls, [("a-1", "Step A.", None)])

    def test_returns_empty_string_for_no_steps(self):
        sut = self._renderer(StubSubagentDelegator(), StubStepFormatter("x"))

        self.assertEqual(sut.render_steps([]), "")

    def test_passes_the_delegators_wrapped_body_to_the_formatter(self):
        delegator = StubSubagentDelegator(wrapped="WRAPPED")
        formatter = StubStepFormatter("FORMATTED")
        sut = self._renderer(delegator, formatter)
        step = StepResult(step_id="a", instance_id="a-1", prompt="Do it.", execution={"mode": "subagent"})

        sut.render_steps([step])

        self.assertEqual(delegator.calls, [("Do it.", {"mode": "subagent"})])
        self.assertEqual(formatter.calls, [("a-1", "WRAPPED", None)])

    def test_passes_the_rejection_reason_to_the_formatter(self):
        formatter = StubStepFormatter("FORMATTED")
        sut = self._renderer(StubSubagentDelegator(), formatter)
        step = StepResult(
            step_id="a", instance_id="a-1", prompt="Do it.", execution={"mode": "inline"},
            rejection_reason="bad value",
        )

        sut.render_steps([step])

        self.assertEqual(formatter.calls, [("a-1", "Do it.", "bad value")])

    @staticmethod
    def _renderer(
        delegator: StubSubagentDelegator,
        formatter: StubStepFormatter,
    ) -> StepRenderer:
        return StepRenderer(
            ready_step_selector=FirstReadyStepSelector(),
            sibling_batch_selector=SiblingBatchStepSelectorFactory().make(),
            single_step_renderer=SingleStepRenderer(
                subagent_delegator=delegator,
                step_formatter=formatter,
            ),
            batch_step_renderer=BatchStepRendererFactory().make(),
        )


if __name__ == "__main__":
    unittest.main()
