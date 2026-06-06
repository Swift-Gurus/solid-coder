"""solid-description: Shared bootstrap that provides a consistent test environment and reusable fixture helpers for unit tests.
solid-category: unit-test
"""

from __future__ import annotations

import sys
import tempfile
import unittest
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
    return make_schema_srp_partial()


def make_schema_srp_metrics() -> dict:
    """Minimal SRP metrics satisfying review/output.schema.json (verbs, cohesion_groups, stakeholders, cross_reference)."""
    return {
        "verbs": {
            "count": 2,
            "table": [
                {"method": "save", "verb": "save"},
                {"method": "load", "verb": "load"},
            ],
        },
        "cohesion_groups": {
            "count": 1,
            "groups": [{"name": "persistence", "variables": ["_db"], "methods": ["save", "load"]}],
            "method_variable_table": [
                {"method": "save", "variables": ["_db"]},
                {"method": "load", "variables": ["_db"]},
            ],
        },
        "stakeholders": {
            "count": 1,
            "table": [{"verb": "save", "stakeholder": "storage"}],
        },
        "cross_reference": [
            {
                "group": "persistence",
                "variables": ["_db"],
                "verbs": ["save", "load"],
                "stakeholder": "storage",
            }
        ],
    }


def make_schema_srp_severe_metrics() -> dict:
    """SRP metrics with 2 cohesion groups — triggers SRP-2 SEVERE band."""
    return {
        "verbs": {
            "count": 4,
            "table": [
                {"method": "save", "verb": "save"},
                {"method": "load", "verb": "load"},
                {"method": "format", "verb": "format"},
                {"method": "notify", "verb": "notify"},
            ],
        },
        "cohesion_groups": {
            "count": 2,
            "groups": [
                {"name": "persistence", "variables": ["_db"], "methods": ["save", "load"]},
                {"name": "notification", "variables": ["_notifier"], "methods": ["format", "notify"]},
            ],
            "method_variable_table": [
                {"method": "save", "variables": ["_db"]},
                {"method": "load", "variables": ["_db"]},
                {"method": "format", "variables": ["_notifier"]},
                {"method": "notify", "variables": ["_notifier"]},
            ],
        },
        "stakeholders": {
            "count": 2,
            "table": [
                {"verb": "save", "stakeholder": "storage"},
                {"verb": "notify", "stakeholder": "notification"},
            ],
        },
        "cross_reference": [
            {"group": "persistence", "variables": ["_db"], "verbs": ["save", "load"], "stakeholder": "storage"},
            {"group": "notification", "variables": ["_notifier"], "verbs": ["format", "notify"], "stakeholder": "notification"},
        ],
    }


def make_schema_srp_partial(units: list | None = None) -> dict:
    """Build a schema-compliant SRP partial output (metrics only, no scoring/findings)."""
    if units is None:
        units = [{"unit_name": "Foo", "unit_kind": "class", "metrics": make_schema_srp_metrics()}]
    return make_partial_output(
        "srp", "Single Responsibility Principle",
        [{"file_path": "/tmp/Foo.swift", "units": units}],
    )


def make_isp_partial(width: int = 3, min_coverage: int = 100, cohesion_groups: int = 1) -> dict:
    """Build a schema-compliant ISP partial output with metrics that satisfy scoring."""
    return make_partial_output(
        "isp", "Interface Segregation Principle",
        [
            {
                "file_path": "/tmp/MyProtocol.swift",
                "units": [
                    {
                        "unit_name": "MyProtocol",
                        "unit_kind": "protocol",
                        "metrics": {
                            "width": width,
                            "min_coverage": min_coverage,
                            "cohesion_groups": cohesion_groups,
                        },
                    }
                ],
            }
        ],
    )


def make_lsp_partial(
    type_checks: int = 0,
    contract_violations: int = 0,
    fatal_error_methods: int = 0,
    empty_methods: int = 0,
) -> dict:
    """Build a schema-compliant LSP partial output with metrics that satisfy scoring."""
    return make_partial_output(
        "lsp", "Liskov Substitution Principle",
        [
            {
                "file_path": "/tmp/MyClass.swift",
                "units": [
                    {
                        "unit_name": "MyClass",
                        "unit_kind": "class",
                        "metrics": {
                            "type_checks": type_checks,
                            "contract_violations": contract_violations,
                            "fatal_error_methods": fatal_error_methods,
                            "empty_methods": empty_methods,
                        },
                    }
                ],
            }
        ],
    )


def make_ocp_partial(sealed_points: int = 0, untestable_dependencies: int = 0, testable_direct_count: int = 0) -> dict:
    """Build a schema-compliant OCP partial output with metrics that satisfy scoring."""
    return make_partial_output(
        "ocp", "Open/Closed Principle",
        [
            {
                "file_path": "/tmp/Bar.swift",
                "units": [
                    {
                        "unit_name": "Bar",
                        "unit_kind": "service",
                        "metrics": {
                            "sealed_variation_points": sealed_points,
                            "untestable_dependencies": untestable_dependencies,
                            "testable_direct_count": testable_direct_count,
                        },
                    }
                ],
            }
        ],
    )


def make_ocp_partial_bad_files() -> dict:
    """OCP partial with files as a string instead of array — fails schema validation."""
    return {
        "agent": "ocp",
        "principle": "Open/Closed Principle",
        "timestamp": "2026-01-01T00:00:00Z",
        "files": "not_an_array",
    }


class SubmitFindingsTestBase(unittest.TestCase):
    """Shared base for submit_findings test classes: handler, temp dir, and path helper."""

    def setUp(self):
        self.handler = make_handler()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def temp_path(self, *parts: str) -> str:
        """Construct an absolute path inside the temp directory."""
        return str(Path(self.tmp.name).joinpath(*parts))

