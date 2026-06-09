"""
solid-description: Verifies error handling modes and structured output parsing for external process execution.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS_DIR))

from hook_utils import SubprocessError, SubprocessJsonRunner, SubprocessAdapter


class TestSubprocessError(unittest.TestCase):
    def test_is_exception(self):
        err = SubprocessError("something failed")
        self.assertIsInstance(err, Exception)
        self.assertIn("something failed", str(err))


class TestStrictCall(unittest.TestCase):
    def _make_boom_adapter(self):
        from hook_callable import CallableAdapting
        def boom():
            raise SubprocessError("subprocess died")
        return CallableAdapting(fn=boom)

    def test_strict_call_propagates_exception(self):
        adapter = self._make_boom_adapter()
        with self.assertRaises(SubprocessError):
            adapter._strict_call()

    def test_safe_call_swallows_exception(self):
        adapter = self._make_boom_adapter()
        self.assertIsNone(adapter._safe_call())

    def test_strict_call_returns_value(self):
        from hook_callable import CallableAdapting
        adapter = CallableAdapting(fn=lambda x: x * 2)
        self.assertEqual(adapter._strict_call(5), 10)


class TestSubprocessJsonRunner(unittest.TestCase):
    def setUp(self):
        self.runner = SubprocessJsonRunner(SubprocessAdapter())

    def test_raises_on_nonzero_exit(self):
        with self.assertRaises(SubprocessError) as ctx:
            self.runner.run(
                [sys.executable, "-c", "import sys; sys.exit(1)"], timeout=10
            )
        self.assertIn("exited", str(ctx.exception))

    def test_raises_on_invalid_json(self):
        with self.assertRaises(SubprocessError) as ctx:
            self.runner.run(
                [sys.executable, "-c", "print('not json')"], timeout=10
            )
        self.assertIn("invalid JSON", str(ctx.exception))

    def test_returns_parsed_json_on_success(self):
        result = self.runner.run(
            [sys.executable, "-c", 'import json; print(json.dumps({"ok": True}))'],
            timeout=10,
        )
        self.assertEqual(result, {"ok": True})


if __name__ == "__main__":
    unittest.main()
