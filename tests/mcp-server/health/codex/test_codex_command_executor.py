"""Checks that child execution diagnostics survive validation failures."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[4] / "mcp-server")

from health.codex.codex_command_executor import CodexCommandExecutor
from subprocess_error import SubprocessError


"""
solid-name: TestCodexCommandExecutor
solid-category: unit-test
solid-spec: [SPEC-067]
solid-description: Verifies successful and failed delegated executions preserve their complete diagnostics before validation.
"""
class TestCodexCommandExecutor(unittest.TestCase):
    def test_records_complete_streams_before_validation(self):
        for succeeded in (True, False):
            with self.subTest(succeeded=succeeded):
                runner = MagicMock()
                stdout = '{"type":"thread.started","thread_id":"child"}\n'
                stderr = "startup detail " * 100 + "required server unavailable"
                runner.run.return_value = succeeded, stdout, stderr
                logger = MagicMock()
                validator = MagicMock()

                def validate(*arguments):
                    self.assertEqual(arguments, (succeeded, stdout, stderr))
                    self.assertEqual(logger.log.call_args_list, [
                        unittest.mock.call("codex.stdout", stdout),
                        unittest.mock.call("codex.stderr", stderr),
                    ])
                    if not succeeded:
                        raise SubprocessError("required server unavailable")

                validator.validate.side_effect = validate
                executor = CodexCommandExecutor(runner, validator, logger)
                if succeeded:
                    executor.execute(["codex", "exec"], 30, None, "/project")
                else:
                    with self.assertRaisesRegex(SubprocessError, "required server unavailable"):
                        executor.execute(["codex", "exec"], 30, None, "/project")
                runner.run.assert_called_once_with(
                    ["codex", "exec"], timeout=30, stdin=None, cwd="/project",
                )
