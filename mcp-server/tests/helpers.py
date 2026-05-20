"""solid-description: Shared bootstrap that provides a consistent test environment and reusable fixture helpers for unit tests.
solid-category: unit-test
"""

import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parents[1]
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

REFS_ROOT = MCP_DIR.parent / "references"

from lib.gateway_tools import make_gateway_handler, GatewayHandler


def make_handler() -> GatewayHandler:
    """Construct a GatewayHandler wired with production defaults for the test refs_root."""
    return make_gateway_handler(REFS_ROOT)


def make_partial_output(agent: str, principle: str, files: list,
                         timestamp: str = "2026-01-01T00:00:00Z") -> dict:
    """Build a minimal partial output document for use in tests."""
    return {"agent": agent, "principle": principle, "timestamp": timestamp, "files": files}


def make_srp_partial(files: list) -> dict:
    """Build a minimal SRP partial output document for use in tests."""
    return make_partial_output("srp", "Single Responsibility Principle", files)


def make_srp_file(metrics: dict) -> dict:
    """Build a single-file fixture with one unit for SRP test scenarios.

    Uses field names matching the SRP review output schema:
    file_path (not path), unit_name (not name), unit_kind (not kind).
    """
    return {
        "file_path": "Foo.swift",
        "units": [{"unit_name": "MyClass", "unit_kind": "class", "metrics": metrics}],
    }


def make_standard_srp_partial() -> dict:
    """Build a standard SRP partial output with one cohesion-compliant unit."""
    return make_srp_partial([make_srp_file({"SRP-2": {"cohesion_groups": 1}})])
