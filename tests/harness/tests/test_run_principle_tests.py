"""
solid-name: TestRunPrincipleTestsCLI
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Validates the principle-test runner CLI's execution-mode handling, confirming unsupported modes are rejected with an error signal and supported modes proceed without spurious error output.
"""

import subprocess
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_CLI = str(_PROJECT_ROOT / "tests" / "run_principle_tests.py")


class TestRunPrincipleTestsCLI(unittest.TestCase):
    def _run(self, extra_args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, _CLI, "--principle", "references/principles/SRP"] + extra_args,
            capture_output=True,
            text=True,
        )

    def test_e2e_mode_exits_1_with_deferral_message(self):
        result = self._run(["--mode", "e2e"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("e2e mode not yet implemented", result.stderr)

    def test_direct_mode_accepts_flag_without_e2e_deferral_message(self):
        result = self._run(["--mode", "direct", "--help"])
        self.assertNotIn("e2e mode not yet implemented", result.stderr)
        self.assertNotIn("e2e mode not yet implemented", result.stdout)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()