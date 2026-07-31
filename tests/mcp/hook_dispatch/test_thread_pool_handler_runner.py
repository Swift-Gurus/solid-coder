"""
solid-name: test_thread_pool_handler_runner
solid-category: unit-test
solid-description: Validates concurrent execution and result order preservation.
"""

from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from thread_pool_handler_runner import ThreadPoolHandlerRunner


class TestThreadPoolHandlerRunner(unittest.TestCase):
    def test_empty_items_returns_empty_list(self):
        result = ThreadPoolHandlerRunner().map(lambda x: x, [])

        self.assertEqual(result, [])

    def test_preserves_input_order_in_results(self):
        result = ThreadPoolHandlerRunner().map(lambda x: x * 2, [1, 2, 3, 4])

        self.assertEqual(result, [2, 4, 6, 8])

    def test_items_run_concurrently_not_sequentially(self):
        """Each task blocks until every task has started — this only completes if
        all N tasks are running at once, proving genuine parallel execution."""
        n = 4
        barrier = threading.Barrier(n, timeout=5)

        def task(i):
            barrier.wait()
            return i

        result = ThreadPoolHandlerRunner().map(task, list(range(n)))

        self.assertEqual(sorted(result), list(range(n)))

    def test_propagates_exception_from_a_task(self):
        def task(i):
            if i == 1:
                raise ValueError("boom")
            return i

        with self.assertRaises(ValueError):
            ThreadPoolHandlerRunner().map(task, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
