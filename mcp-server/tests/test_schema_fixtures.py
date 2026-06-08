"""
solid-description: Verifies principle metric schema validation and rejection of incomplete submissions.
solid-category: unit-test
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tests.helpers import (
    SubmitFindingsTestBase,
    make_partial_output,
    make_unit,
    make_file,
)

_REFS = Path(__file__).resolve().parents[2] / "references" / "principles"
_GATEWAY = str(Path(__file__).resolve().parents[1] / "gateway.py")


def _principle_metrics_schema(principle: str) -> dict:
    """Return the per-principle metrics schema (now describes only the metrics sub-object)."""
    return json.loads((_REFS / principle / "review" / "output.schema.json").read_text())


def _validate(metrics: dict, subschema: dict) -> dict:
    """Validate metrics dict against a subschema via the validate_phase_output gateway tool."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as mf:
        json.dump(metrics, mf)
        metrics_path = mf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
        json.dump(subschema, sf)
        schema_path = sf.name
    result = subprocess.run(
        [sys.executable, _GATEWAY, "validate_phase_output",
         "--json-path", metrics_path, "--schema-path", schema_path],
        capture_output=True, text=True,
    )
    Path(metrics_path).unlink(missing_ok=True)
    Path(schema_path).unlink(missing_ok=True)
    return json.loads(result.stdout)


def _make_unit_metrics(principle: str, metrics: dict) -> dict:
    """Wrap metrics in the new {principle: metrics} shape for a unit."""
    return {principle: metrics}


class SchemaFixtureTestBase(SubmitFindingsTestBase):
    """Parameterised base that generates schema-fixture tests for any principle.

    Subclasses set:
      principle           — folder name under references/principles/
      compliant_metrics   — {var: {value: N}} dict that should score COMPLIANT
      severe_metrics      — {var: {value: N}} dict that should score SEVERE
      missing_field       — one required variable name to delete for the missing-field test
    """

    principle: str = ""
    unit_kind: str = "class"
    compliant_metrics: dict = {}
    severe_metrics: dict = {}
    missing_field: str = ""

    def setUp(self) -> None:
        super().setUp()
        if not self.principle:
            self.skipTest("SchemaFixtureTestBase is abstract — subclasses must set principle")

    def _schema(self) -> dict:
        return _principle_metrics_schema(self.principle)

    def _partial(self, metrics: dict) -> dict:
        unit_metrics = _make_unit_metrics(self.principle, metrics)
        return make_partial_output([
            make_file("/tmp/Foo.swift", [make_unit("Foo", self.unit_kind, unit_metrics)])
        ])

    def test_compliant_metrics_are_schema_valid(self):
        result = _validate(self.compliant_metrics, self._schema())
        self.assertTrue(result["valid"], result.get("error"))

    def test_severe_metrics_are_schema_valid(self):
        result = _validate(self.severe_metrics, self._schema())
        self.assertTrue(result["valid"], result.get("error"))

    def test_missing_required_field_fails_schema(self):
        bad = dict(self.compliant_metrics)
        bad.pop(self.missing_field, None)
        result = _validate(bad, self._schema())
        self.assertFalse(result["valid"])

    def test_submit_findings_rejects_incomplete_metrics(self):
        bad = dict(self.compliant_metrics)
        bad.pop(self.missing_field, None)
        result = self.handler.submit_findings(
            self._partial(bad),
            self.temp_path("out.json"),
        )
        self.assertIn("error", result)
        self.assertIn(self.missing_field, result["error"])


class TestSRPSchemaFixtures(SchemaFixtureTestBase):
    principle = "SRP"
    compliant_metrics = {"verb_count": {"value": 2}, "cohesion_groups": {"value": 1}, "stakeholder_count": {"value": 1}}
    severe_metrics = {"verb_count": {"value": 4}, "cohesion_groups": {"value": 2}, "stakeholder_count": {"value": 2}}
    missing_field = "cohesion_groups"


class TestOCPSchemaFixtures(SchemaFixtureTestBase):
    principle = "OCP"
    compliant_metrics = {"sealed_variation_points": {"value": 0}, "untestable_dependencies": {"value": 0}, "testable_direct_count": {"value": 0}}
    severe_metrics = {"sealed_variation_points": {"value": 2}, "untestable_dependencies": {"value": 1}, "testable_direct_count": {"value": 0}}
    missing_field = "sealed_variation_points"


class TestISPSchemaFixtures(SchemaFixtureTestBase):
    principle = "ISP"
    unit_kind = "protocol"
    compliant_metrics = {"width": {"value": 3}, "min_coverage": {"value": 100}, "cohesion_groups": {"value": 1}}
    severe_metrics = {"width": {"value": 10}, "min_coverage": {"value": 40}, "cohesion_groups": {"value": 3}}
    missing_field = "width"

    def _partial(self, metrics: dict) -> dict:
        unit_metrics = _make_unit_metrics(self.principle, metrics)
        return make_partial_output([
            make_file("/tmp/MyProtocol.swift", [make_unit("MyProtocol", "protocol", unit_metrics)])
        ])


class TestLSPSchemaFixtures(SchemaFixtureTestBase):
    principle = "LSP"
    compliant_metrics = {"type_checks": {"value": 0}, "contract_violations": {"value": 0}, "fatal_error_methods": {"value": 0}, "empty_methods": {"value": 0}}
    severe_metrics = {"type_checks": {"value": 3}, "contract_violations": {"value": 1}, "fatal_error_methods": {"value": 1}, "empty_methods": {"value": 0}}
    missing_field = "type_checks"


class TestDRYSchemaFixtures(SchemaFixtureTestBase):
    principle = "DRY"
    compliant_metrics = {"reuse_misses": {"value": 0}, "duplicate_sites": {"value": 0}, "missing_abstractions": {"value": 0}}
    severe_metrics = {"reuse_misses": {"value": 1}, "duplicate_sites": {"value": 2}, "missing_abstractions": {"value": 1}}
    missing_field = "reuse_misses"


if __name__ == "__main__":
    unittest.main()
