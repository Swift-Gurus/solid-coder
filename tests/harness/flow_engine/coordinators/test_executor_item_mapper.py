"""
solid-name: test_executor_item_mapper
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies bounded concurrent item execution and source-ordered result collection.
"""

import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.executor_item_mapper import ExecutorItemMapper
from harness.thread_pool_executor_factory import ThreadPoolExecutorFactory


class TestExecutorItemMapper(unittest.TestCase):
    def test_limits_concurrency_and_returns_results_in_source_order(self) -> None:
        lock = threading.Lock()
        active_count = 0
        maximum_active_count = 0

        def map_item(item: int) -> str:
            nonlocal active_count, maximum_active_count
            with lock:
                active_count += 1
                maximum_active_count = max(maximum_active_count, active_count)
            time.sleep(0.03)
            with lock:
                active_count -= 1
            return f"result-{item}"

        results = ExecutorItemMapper(ThreadPoolExecutorFactory()).map(
            map_item,
            [1, 2, 3, 4],
            max_workers=2,
        )

        self.assertEqual(maximum_active_count, 2)
        self.assertEqual(
            results,
            ["result-1", "result-2", "result-3", "result-4"],
        )


if __name__ == "__main__":
    unittest.main()
