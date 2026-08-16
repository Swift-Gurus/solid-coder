"""Tests flow-run parallel-session configuration wiring."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server" / "health" / "config"))

from flow_engine_config import FlowEngineConfig  # noqa: E402
from pipeline.flow_run_creator import FlowRunCreator  # noqa: E402
from solid_coder_config import SolidCoderConfig  # noqa: E402


"""
solid-name: TestFlowRunCreatorParallelSessions
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies the production flow composition receives configured session concurrency.
"""
class TestFlowRunCreatorParallelSessions(unittest.TestCase):
    def test_passes_configured_maximum_to_orchestrator_factory(self) -> None:
        config = SolidCoderConfig(
            flow_engine=FlowEngineConfig(max_parallel_sessions=7)
        )
        expected_orchestrator = object()

        with patch(
            "pipeline.flow_run_creator.FlowRunOrchestratorFactory"
        ) as factory:
            factory.return_value.build.return_value = expected_orchestrator
            result = FlowRunCreator(
                plugin_root=Path("/plugin"),
                config_loader=lambda: config,
            ).create(transport=object())

        self.assertIs(result, expected_orchestrator)
        self.assertEqual(
            factory.call_args.kwargs["session_delegate_max_workers"],
            7,
        )


if __name__ == "__main__":
    unittest.main()
