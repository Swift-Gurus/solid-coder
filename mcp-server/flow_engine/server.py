#!/usr/bin/env python3
"""Starts the dedicated solid-coder flow-engine MCP server."""

import sys
from pathlib import Path


_SERVER_DIRECTORY = Path(__file__).resolve().parent
_MCP_SERVER_DIRECTORY = _SERVER_DIRECTORY.parent
_PLUGIN_ROOT = _MCP_SERVER_DIRECTORY.parent
_HEALTH_CONFIG_DIRECTORY = _MCP_SERVER_DIRECTORY / "health" / "config"
for _directory in (_MCP_SERVER_DIRECTORY, _HEALTH_CONFIG_DIRECTORY):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from flow_engine.application_factory import FlowEngineApplicationFactory  # noqa: E402
from pipeline.flow_result_renderer_creator import FlowResultRendererCreator  # noqa: E402
from pipeline.flow_run_creator import FlowRunCreator  # noqa: E402


def main() -> None:
    FlowEngineApplicationFactory(
        plugin_root=_PLUGIN_ROOT,
        flow_run_creator=FlowRunCreator(_PLUGIN_ROOT),
        flow_renderer_creator=FlowResultRendererCreator(),
    ).make().run()


if __name__ == "__main__":
    main()
