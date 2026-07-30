"""
solid-name: test_interpolation_guard
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests turning an InterpolationError raised by a callable into an error message.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.interpolation_error import InterpolationError
from harness.interpolation_guard import InterpolationGuard


class TestInterpolationGuard(unittest.TestCase):

    def setUp(self):
        self.sut = InterpolationGuard()

    def test_returns_the_callables_value_and_no_error_on_success(self):
        value, error = self.sut.guard(lambda: 42)

        self.assertEqual(value, 42)
        self.assertIsNone(error)

    def test_returns_none_and_the_error_message_when_interpolation_error_is_raised(self):
        def _raise():
            raise InterpolationError("bad reference")

        value, error = self.sut.guard(_raise)

        self.assertIsNone(value)
        self.assertEqual(error, "bad reference")

    def test_does_not_catch_other_exception_types(self):
        def _raise():
            raise ValueError("not an interpolation error")

        with self.assertRaises(ValueError):
            self.sut.guard(_raise)


if __name__ == "__main__":
    unittest.main()
