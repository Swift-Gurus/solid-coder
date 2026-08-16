"""Tests validation of flow-engine parallel-session configuration."""

import sys
import unittest
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server" / "health" / "config"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "mcp-server" / "hooks"))

from _config_section_stub import ConfigSectionStub  # noqa: E402
from hc_config_schema import load_config  # noqa: E402
from solid_coder_config_error import SolidCoderConfigError  # noqa: E402


"""
solid-name: TestFlowEngineParallelSessionConfigValidation
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies rejection of an unsafe bounded session concurrency setting.
"""
class TestFlowEngineParallelSessionConfigValidation(unittest.TestCase):
    def test_rejects_non_positive_max_parallel_sessions(self) -> None:
        with ConfigSectionStub(flow_engine={"max_parallel_sessions": 0}):
            with self.assertRaises(SolidCoderConfigError) as context:
                load_config()

        self.assertIn(
            "flow_engine.max_parallel_sessions",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
