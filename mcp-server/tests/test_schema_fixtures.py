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
    make_schema_srp_metrics,
    make_schema_srp_severe_metrics,
)

_REFS = Path(__file__).resolve().parents[2] / "references" / "principles"
_GATEWAY = str(Path(__file__).resolve().parents[1] / "gateway.py")


def _metrics_subschema(principle: str) -> dict:
    schema = json.loads((_REFS / principle / "review" / "output.schema.json").read_text())
    return (
        schema["properties"]["files"]["items"]
        ["properties"]["units"]["items"]
        ["properties"]["metrics"]
    )


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


class SchemaFixtureTestBase(SubmitFindingsTestBase):
    """Parameterised base that generates 4 schema-fixture tests for any principle.

    Subclasses set:
      principle           — folder name under references/principles/
      agent               — agent const in the schema (e.g. 'srp')
      principle_name      — principle const in the schema (e.g. 'Single Responsibility Principle')
      compliant_metrics   — metrics dict that should pass schema and score COMPLIANT
      severe_metrics      — metrics dict that should pass schema and score SEVERE
      missing_field       — one required field name to delete for the missing-field test
      incomplete_metrics  — metrics dict missing at least one required field
    """

    principle: str = ""
    agent: str = ""
    principle_name: str = ""
    compliant_metrics: dict = {}
    severe_metrics: dict = {}
    missing_field: str = ""
    incomplete_metrics: dict = {}

    def setUp(self) -> None:
        super().setUp()
        if not self.principle:
            self.skipTest("SchemaFixtureTestBase is abstract — subclasses must set principle")

    def _subschema(self) -> dict:
        return _metrics_subschema(self.principle)

    def _partial(self, metrics: dict) -> dict:
        return make_partial_output(self.agent, self.principle_name, [
            {"file_path": "/tmp/Foo.swift", "units": [
                {"unit_name": "Foo", "unit_kind": "class", "metrics": metrics}
            ]}
        ])

    def test_compliant_metrics_are_schema_valid(self):
        result = _validate(self.compliant_metrics, self._subschema())
        self.assertTrue(result["valid"], result.get("error"))

    def test_severe_metrics_are_schema_valid(self):
        result = _validate(self.severe_metrics, self._subschema())
        self.assertTrue(result["valid"], result.get("error"))

    def test_missing_required_field_fails_schema(self):
        bad = dict(self.compliant_metrics)
        bad.pop(self.missing_field, None)
        result = _validate(bad, self._subschema())
        self.assertFalse(result["valid"])

    def test_submit_findings_rejects_incomplete_metrics(self):
        result = self.handler.submit_findings(
            self._partial(self.incomplete_metrics),
            self.temp_path("out.json"),
        )
        self.assertIn("error", result)
        self.assertIn(self.missing_field, result["error"])


class TestSRPSchemaFixtures(SchemaFixtureTestBase):
    principle = "SRP"
    agent = "srp"
    principle_name = "Single Responsibility Principle"
    compliant_metrics = make_schema_srp_metrics()
    severe_metrics = make_schema_srp_severe_metrics()
    missing_field = "cohesion_groups"
    incomplete_metrics = {k: v for k, v in make_schema_srp_metrics().items() if k != "cohesion_groups"}


class TestOCPSchemaFixtures(SchemaFixtureTestBase):
    principle = "OCP"
    agent = "ocp"
    principle_name = "Open/Closed Principle"
    compliant_metrics = {"sealed_variation_points": 0, "untestable_dependencies": 0, "testable_direct_count": 0}
    severe_metrics = {"sealed_variation_points": 2, "untestable_dependencies": 1, "testable_direct_count": 0}
    missing_field = "sealed_variation_points"
    incomplete_metrics = {"untestable_dependencies": 0, "testable_direct_count": 0}


class TestISPSchemaFixtures(SchemaFixtureTestBase):
    principle = "ISP"
    agent = "isp"
    principle_name = "Interface Segregation Principle"
    compliant_metrics = {"width": 3, "min_coverage": 100, "cohesion_groups": 1}
    severe_metrics = {"width": 10, "min_coverage": 40, "cohesion_groups": 3}
    missing_field = "width"
    incomplete_metrics = {"min_coverage": 100, "cohesion_groups": 1}

    def _partial(self, metrics: dict) -> dict:
        return make_partial_output(self.agent, self.principle_name, [
            {"file_path": "/tmp/MyProtocol.swift", "units": [
                {"unit_name": "MyProtocol", "unit_kind": "protocol", "metrics": metrics}
            ]}
        ])


class TestLSPSchemaFixtures(SchemaFixtureTestBase):
    principle = "LSP"
    agent = "lsp"
    principle_name = "Liskov Substitution Principle"
    compliant_metrics = {"type_checks": 0, "contract_violations": 0, "fatal_error_methods": 0, "empty_methods": 0}
    severe_metrics = {"type_checks": 3, "contract_violations": 1, "fatal_error_methods": 1, "empty_methods": 0}
    missing_field = "type_checks"
    incomplete_metrics = {"contract_violations": 0, "fatal_error_methods": 0, "empty_methods": 0}


if __name__ == "__main__":
    unittest.main()
