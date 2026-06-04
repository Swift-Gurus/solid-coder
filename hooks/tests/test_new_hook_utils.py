"""
solid-description: Verifies that subprocess error handling, JSON field parsing, and callable adapter invocation modes behave correctly under normal and failure conditions.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS_DIR))

from hook_utils import SubprocessError, parse_json_field, _run_subprocess_to_json


class TestSubprocessError(unittest.TestCase):
    def test_is_exception(self):
        err = SubprocessError("something failed")
        self.assertIsInstance(err, Exception)
        self.assertIn("something failed", str(err))


class TestParseJsonField(unittest.TestCase):
    def test_returns_value_when_key_and_type_match(self):
        result = parse_json_field('{"corrected_content": "hello"}', "corrected_content", str)
        self.assertEqual(result, "hello")

    def test_returns_none_when_key_missing(self):
        result = parse_json_field('{"other_key": "hello"}', "corrected_content", str)
        self.assertIsNone(result)

    def test_returns_none_when_type_mismatch(self):
        result = parse_json_field('{"violations": "not-a-list"}', "violations", list)
        self.assertIsNone(result)

    def test_returns_list_when_type_matches(self):
        result = parse_json_field('{"violations": [1, 2, 3]}', "violations", list)
        self.assertEqual(result, [1, 2, 3])

    def test_strips_markdown_fences(self):
        raw = '\n{"corrected_content": "stripped"}\n'
        result = parse_json_field(raw, "corrected_content", str)
        self.assertEqual(result, "stripped")

    def test_returns_none_on_invalid_json(self):
        result = parse_json_field("not json at all", "key", str)
        self.assertIsNone(result)

    def test_returns_none_on_empty_string(self):
        result = parse_json_field("", "key", str)
        self.assertIsNone(result)


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


class TestRunSubprocessToJson(unittest.TestCase):
    def test_raises_on_nonzero_exit(self):
        with self.assertRaises(SubprocessError) as ctx:
            _run_subprocess_to_json(
                [sys.executable, "-c", "import sys; sys.exit(1)"], timeout=10
            )
        self.assertIn("exited 1", str(ctx.exception))

    def test_raises_on_invalid_json(self):
        with self.assertRaises(SubprocessError) as ctx:
            _run_subprocess_to_json(
                [sys.executable, "-c", "print('not json')"], timeout=10
            )
        self.assertIn("invalid JSON", str(ctx.exception))

    def test_returns_parsed_json_on_success(self):
        result = _run_subprocess_to_json(
            [sys.executable, "-c", 'import json; print(json.dumps({"ok": True}))'],
            timeout=10,
        )
        self.assertEqual(result, {"ok": True})


if __name__ == "__main__":
    unittest.main()
