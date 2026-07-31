"""
solid-name: test_parallel_hook_dispatcher
solid-category: unit-test
solid-description: Validates concurrent hook decision dispatch with exception isolation and complete result aggregation.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from concurrent_handler_executor import ConcurrentHandlerExecutor
from hook_dispatch_doubles import (
    AllowHandler,
    AllowHandlerWithContext,
    DenyHandler,
    NotApplicableHandler,
    RaisingHandler,
    SleepingHandler,
)
from parallel_hook_dispatcher import ParallelHookDispatcher


def _build(handlers) -> ParallelHookDispatcher:
    return ParallelHookDispatcher(executor=ConcurrentHandlerExecutor(handlers=handlers))


class TestParallelHookDispatcher(unittest.TestCase):
    def test_no_handlers_allows(self):
        dispatcher = _build([])

        decision = dispatcher.dispatch({})

        self.assertTrue(decision.allow)

    def test_not_applicable_handlers_are_skipped_entirely(self):
        dispatcher = _build([NotApplicableHandler(), AllowHandler()])

        decision = dispatcher.dispatch({})

        self.assertTrue(decision.allow)

    def test_single_denial_blocks_with_its_reason(self):
        dispatcher = _build([AllowHandler(), DenyHandler("flow left in_progress")])

        decision = dispatcher.dispatch({})

        self.assertFalse(decision.allow)
        self.assertEqual(decision.reason, "flow left in_progress")

    def test_reasons_from_every_denying_handler_are_aggregated(self):
        dispatcher = _build([DenyHandler("reason A"), DenyHandler("reason B")])

        decision = dispatcher.dispatch({})

        self.assertFalse(decision.allow)
        self.assertIn("reason A", decision.reason)
        self.assertIn("reason B", decision.reason)

    def test_a_raising_handler_fails_open_and_does_not_block_other_handlers_decision(self):
        dispatcher = _build([RaisingHandler(), AllowHandler()])

        decision = dispatcher.dispatch({})

        self.assertTrue(decision.allow)

    def test_additional_context_surfaces_even_on_allow(self):
        dispatcher = _build([
            DenyHandler("blocked", additional_context=None),
            AllowHandlerWithContext("reminder"),
        ])

        decision = dispatcher.dispatch({})

        self.assertFalse(decision.allow)
        self.assertEqual(decision.additional_context, "reminder")

    def test_wall_clock_reflects_the_slowest_handler_not_the_sum(self):
        """Three handlers sleeping ~0.3s each must finish in ~0.3s total if run in
        parallel — a sequential implementation would take ~0.9s."""
        dispatcher = _build([SleepingHandler(0.3), SleepingHandler(0.3), SleepingHandler(0.3)])

        start = time.monotonic()
        decision = dispatcher.dispatch({})
        elapsed = time.monotonic() - start

        self.assertTrue(decision.allow)
        self.assertLess(elapsed, 0.6)


if __name__ == "__main__":
    unittest.main()
