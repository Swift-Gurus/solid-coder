"""solid-description: Shared bootstrap that provides a consistent test environment and reusable fixture helpers for unit tests.
solid-category: unit-test
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parents[2] / "mcp-server"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

REFS_ROOT = MCP_DIR.parent / "references"

from lib.gateway_tools import GatewayHandler, GatewayHandlerFactory


def make_handler() -> GatewayHandler:
    """Construct a GatewayHandler wired with production defaults for the test refs_root."""
    return GatewayHandlerFactory().make(REFS_ROOT)


def make_partial_output(files: list, timestamp: str = "2026-01-01T00:00:00Z") -> dict:
    """Build a minimal partial output document for use in tests."""
    return {"timestamp": timestamp, "files": files}


def make_unit(unit_name: str, unit_kind: str, metrics: dict) -> dict:
    """Build a single unit dict for use in file fixtures."""
    audited_metrics = {
        principle: {
            name: (
                make_metric(measurement["value"])
                if set(measurement) == {"value"}
                else measurement
            )
            for name, measurement in measurements.items()
        }
        for principle, measurements in metrics.items()
    }
    return {
        "unit_name": unit_name,
        "unit_kind": unit_kind,
        "metrics": audited_metrics,
    }


def make_file(file_path: str, units: list) -> dict:
    """Build a single file fixture."""
    return {"file_path": file_path, "units": units}


def make_metric(value, is_exception: bool = False) -> dict:
    """Build one auditable metric measurement for model-facing fixtures."""
    return {
        "value": value,
        "is_exception": is_exception,
        "additional_info": {
            "reasoning": "Fixture measurement selected for this test scenario.",
            "evidence": f"Fixture metric value: {value}",
        },
    }


# ── SRP fixtures ──────────────────────────────────────────────────────────────

def make_schema_srp_metrics() -> dict:
    """Minimal SRP metrics in the new {principle: {var: {value: N}}} format — scores COMPLIANT."""
    return {
        "SRP": {
            "verb_count":        make_metric(2),
            "cohesion_groups":   make_metric(1),
            "stakeholder_count": make_metric(1),
        }
    }


def make_schema_srp_severe_metrics() -> dict:
    """SRP metrics with 2 cohesion groups and 4 verbs — triggers SRP-1 and SRP-2 SEVERE bands."""
    return {
        "SRP": {
            "verb_count":        make_metric(4),
            "cohesion_groups":   make_metric(2),
            "stakeholder_count": make_metric(2),
        }
    }


def make_schema_srp_partial(units: list | None = None) -> dict:
    """Build a schema-compliant SRP partial output (metrics only, no violations)."""
    if units is None:
        units = [make_unit("Foo", "class", make_schema_srp_metrics())]
    return make_partial_output([make_file("/tmp/Foo.swift", units)])


# ── OCP fixtures ──────────────────────────────────────────────────────────────

def make_ocp_partial(
    sealed_points: int = 0,
    untestable_dependencies: int = 0,
    testable_direct_count: int = 0,
) -> dict:
    """Build a schema-compliant OCP partial output with metrics that satisfy scoring."""
    metrics = {
        "OCP": {
            "sealed_variation_points": make_metric(sealed_points),
            "untestable_dependencies":  make_metric(untestable_dependencies),
            "testable_direct_count":    make_metric(testable_direct_count),
        }
    }
    return make_partial_output([make_file("/tmp/Bar.swift", [make_unit("Bar", "class", metrics)])])


def make_ocp_partial_bad_files() -> dict:
    """OCP partial with files as a string instead of array — fails schema validation."""
    return {"timestamp": "2026-01-01T00:00:00Z", "files": "not_an_array"}


# ── ISP fixtures ──────────────────────────────────────────────────────────────

def make_isp_partial(
    width: int = 3,
    min_coverage: int = 100,
    cohesion_groups: int = 1,
) -> dict:
    """Build a schema-compliant ISP partial output with metrics that satisfy scoring."""
    metrics = {
        "ISP": {
            "width":           make_metric(width),
            "min_coverage":    make_metric(min_coverage),
            "cohesion_groups": make_metric(cohesion_groups),
        }
    }
    return make_partial_output([
        make_file("/tmp/MyProtocol.swift", [make_unit("MyProtocol", "protocol", metrics)])
    ])


# ── LSP fixtures ──────────────────────────────────────────────────────────────

def make_lsp_partial(
    type_checks: int = 0,
    contract_violations: int = 0,
    fatal_error_methods: int = 0,
    empty_methods: int = 0,
) -> dict:
    """Build a schema-compliant LSP partial output with metrics that satisfy scoring."""
    metrics = {
        "LSP": {
            "type_checks":          make_metric(type_checks),
            "contract_violations":  make_metric(contract_violations),
            "fatal_error_methods":  make_metric(fatal_error_methods),
            "empty_methods":        make_metric(empty_methods),
        }
    }
    return make_partial_output([
        make_file("/tmp/MyClass.swift", [make_unit("MyClass", "class", metrics)])
    ])


# ── Legacy alias (kept for callers that haven't migrated) ──────────────────────

def make_srp_partial(files: list) -> dict:
    """Build a minimal SRP partial output from an already-structured files list."""
    return make_partial_output(files)


def make_srp_file(metrics: dict) -> dict:
    """Build a single-file fixture with one unit. metrics should use the new {SRP: {...}} shape."""
    return make_file("Foo.swift", [make_unit("MyClass", "class", metrics)])


def make_standard_srp_partial() -> dict:
    """Build a standard SRP partial output with one cohesion-compliant unit."""
    return make_schema_srp_partial()


class SubmitFindingsTestBase(unittest.TestCase):
    """
    solid-name: SubmitFindingsTestBase
    solid-category: unit-test
    solid-description: Provides shared submission-test setup and temporary-path support.
    """

    def setUp(self):
        self.handler = make_handler()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def temp_path(self, *parts: str) -> str:
        """Construct an absolute path inside the temp directory."""
        return str(Path(self.tmp.name).joinpath(*parts))
