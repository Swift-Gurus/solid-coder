"""Tests default flow-engine parallel-session configuration."""

import sys
import unittest
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server" / "health" / "config"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "mcp-server" / "hooks"))

from _config_section_stub import ConfigSectionStub  # noqa: E402
from hc_config_schema import load_config  # noqa: E402


"""
solid-name: TestFlowEngineParallelSessionConfigDefault
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies the default bounded session concurrency setting.
"""
class TestFlowEngineParallelSessionConfigDefault(unittest.TestCase):
    def test_defaults_max_parallel_sessions_to_four(self) -> None:
        with ConfigSectionStub():
            config = load_config()

        self.assertEqual(config.flow_engine.max_parallel_sessions, 4)


if __name__ == "__main__":
    unittest.main()
