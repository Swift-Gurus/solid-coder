"""
solid-name: test_concurrent_handler_executor
solid-category: unit-test
solid-description: Tests that applicable handlers are executed and their decisions are collected.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from concurrent_handler_executor import ConcurrentHandlerExecutor
from hook_dispatch_doubles import PassthroughSafeRunner, RecordingSafeRunner, SerialPoolRunner, StubHandler
from hook_decision import HookDecision


class TestConcurrentHandlerExecutor(unittest.TestCase):
    def test_only_applicable_handlers_are_submitted_to_the_pool(self):
        applicable = StubHandler(applicable=True, decision=HookDecision(allow=True), name="applicable")
        skipped = StubHandler(
            applicable=False, decision=HookDecision(allow=False, reason="should never appear"), name="skipped",
        )
        pool = SerialPoolRunner()
        executor = ConcurrentHandlerExecutor(
            handlers=[applicable, skipped], safe_runner=PassthroughSafeRunner(), pool_runner=pool,
        )

        decisions = executor.run({})

        self.assertEqual(pool.received_items, [applicable])
        self.assertEqual(decisions, [HookDecision(allow=True)])

    def test_no_applicable_handlers_returns_empty_without_invoking_pool(self):
        pool = SerialPoolRunner()
        executor = ConcurrentHandlerExecutor(
            handlers=[StubHandler(applicable=False, decision=HookDecision(allow=True), name="skipped")],
            safe_runner=PassthroughSafeRunner(),
            pool_runner=pool,
        )

        decisions = executor.run({})

        self.assertEqual(decisions, [])
        self.assertEqual(pool.received_items, [])

    def test_delegates_invocation_through_the_safe_runner(self):
        handler = StubHandler(applicable=True, decision=HookDecision(allow=False, reason="unused"), name="h1")
        safe_runner = RecordingSafeRunner()
        executor = ConcurrentHandlerExecutor(
            handlers=[handler], safe_runner=safe_runner, pool_runner=SerialPoolRunner(),
        )

        decisions = executor.run({})

        self.assertEqual(safe_runner.calls, ["h1"])
        self.assertEqual(decisions, [HookDecision(allow=True)])


if __name__ == "__main__":
    unittest.main()
