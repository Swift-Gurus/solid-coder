"""
solid-description: Tests function execution logging with entry, exit, and error tracking.
solid-category: unit-test
"""

import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
MCP_DIR = HOOKS_DIR.parent
sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(MCP_DIR / "utils"))

from debug_logger import DebugLogger, Observing


def _make_logger(tmp_dir: Path) -> DebugLogger:
    return DebugLogger(project_dir_fn=lambda: tmp_dir)


class DebugLoggerTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.logger = _make_logger(self.tmp)

    def _lines(self):
        log = self.tmp / "debug.log"
        return log.read_text().splitlines() if log.exists() else []


class TestDebugLogger(DebugLoggerTestBase):
    def test_log_creates_file(self):
        self.logger.log("my.func", "ENTER")
        self.assertTrue((self.tmp / "debug.log").exists())

    def test_log_format(self):
        self.logger.log("my.func", "ENTER")
        line = self._lines()[0]
        self.assertRegex(line, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z my\.func ENTER$")

    def test_multiple_entries_appended(self):
        self.logger.log("a", "ENTER")
        self.logger.log("a", "EXIT")
        self.assertEqual(len(self._lines()), 2)

    def test_never_raises_on_bad_path(self):
        bad_logger = DebugLogger(project_dir_fn=lambda: Path("/nonexistent/path/that/cannot/be/created"))
        bad_logger.log("x", "ENTER")  # must not raise


class TestObserving(DebugLoggerTestBase):
    def test_enter_and_exit_on_success(self):
        @Observing("fn.ok", logger=self.logger)
        def ok():
            return 42

        result = ok()
        self.assertEqual(result, 42)
        lines = self._lines()
        self.assertEqual(len(lines), 2)
        self.assertIn("fn.ok() ENTER", lines[0])
        self.assertIn("fn.ok EXIT", lines[1])

    def test_error_logged_and_exception_reraises(self):
        @Observing("fn.boom", logger=self.logger)
        def boom():
            raise ValueError("oops")

        with self.assertRaises(ValueError):
            boom()
        lines = self._lines()
        self.assertEqual(len(lines), 2)
        self.assertIn("fn.boom() ENTER", lines[0])
        self.assertIn("fn.boom ERROR ValueError: oops", lines[1])

    def test_log_args_false_no_args_in_enter(self):
        @Observing("fn.noargs", log_args=False, logger=self.logger)
        def fn(x, y=1):
            pass

        fn(99, y=2)
        self.assertIn("fn.noargs ENTER", self._lines()[0])
        self.assertNotIn("99", self._lines()[0])

    def test_log_args_true_is_default(self):
        @Observing("fn.default", logger=self.logger)
        def fn(x):
            pass

        fn(42)
        self.assertIn("42", self._lines()[0])

    def test_log_args_true_includes_repr(self):
        @Observing("fn.args", log_args=True, logger=self.logger)
        def fn(x, y=1):
            pass

        fn(99, y=2)
        enter_line = self._lines()[0]
        self.assertIn("99", enter_line)
        self.assertIn("y=2", enter_line)

    def test_functools_wraps_preserves_name(self):
        @Observing("fn.named", logger=self.logger)
        def my_function():
            pass

        self.assertEqual(my_function.__name__, "my_function")


if __name__ == "__main__":
    unittest.main()
