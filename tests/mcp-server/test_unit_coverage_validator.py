"""
solid-name: TestUnitCoverageValidator
solid-category: unit-test
solid-description: Verifies code unit consistency across SOLID principle definitions.
"""

import unittest
from findings.unit_coverage_validator import UnitCoverageValidator, _extract_unit_names


def _pop(units: list) -> dict:
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "files": [{"file_path": "/F.swift", "units": [
            {"unit_name": u, "unit_kind": "class", "metrics": {}} for u in units
        ]}],
    }


def _empty() -> dict:
    return {"timestamp": "2026-01-01T00:00:00Z", "files": [{"file_path": "/F.swift", "units": []}]}


def _malformed() -> dict:
    return {"timestamp": "2026-01-01T00:00:00Z", "files": "not_a_list"}


class TestExtractUnitNames(unittest.TestCase):
    def test_returns_names_from_valid_payload(self):
        self.assertEqual(["Foo"], _extract_unit_names(_pop(["Foo"])))

    def test_returns_empty_list_for_empty_units(self):
        self.assertEqual([], _extract_unit_names(_empty()))

    def test_returns_none_for_malformed_files(self):
        self.assertIsNone(_extract_unit_names(_malformed()))


class TestUnitCoverageValidatorCrossPrinciple(unittest.TestCase):
    def setUp(self):
        self._v = UnitCoverageValidator()

    def test_isp_empty_while_srp_populated_rejected(self):
        result = self._v._validate_cross_principle({
            "SRP": _pop(["ProductCatalog"]),
            "ISP": _empty(),
        })
        self.assertIsNotNone(result)
        self.assertIn("ISP", result["principles_with_no_units"])

    def test_multiple_skipped_all_listed(self):
        result = self._v._validate_cross_principle({
            "SRP": _pop(["Foo"]),
            "ISP": _empty(),
            "OCP": _empty(),
        })
        self.assertIsNotNone(result)
        self.assertIn("ISP", result["principles_with_no_units"])
        self.assertIn("OCP", result["principles_with_no_units"])

    def test_expected_units_in_response(self):
        result = self._v._validate_cross_principle({
            "SRP": _pop(["Bar", "Baz"]),
            "ISP": _empty(),
        })
        self.assertIn("Bar", result["expected_units"])
        self.assertIn("Baz", result["expected_units"])

    def test_all_solid_populated_passes(self):
        result = self._v._validate_cross_principle({
            "SRP": _pop(["Foo"]),
            "OCP": _pop(["Foo"]),
            "ISP": _pop(["Foo"]),
            "LSP": _pop(["Foo"]),
            "DRY": _pop(["Foo"]),
        })
        self.assertIsNone(result)

    def test_all_solid_empty_passes(self):
        result = self._v._validate_cross_principle({
            "SRP": _empty(), "OCP": _empty(), "ISP": _empty(),
        })
        self.assertIsNone(result)

    def test_empty_submissions_passes(self):
        self.assertIsNone(self._v._validate_cross_principle({}))

    def test_conditional_principle_excluded(self):
        result = self._v._validate_cross_principle({
            "SRP": _pop(["Foo"]),
            "swiftui": _empty(),
            "testing": _empty(),
            "code-smells": _empty(),
        })
        self.assertIsNone(result)

    def test_malformed_payload_excluded_not_flagged(self):
        result = self._v._validate_cross_principle({
            "SRP": _pop(["Foo"]),
            "OCP": _malformed(),
        })
        self.assertIsNone(result)

    def test_dry_skip_detected(self):
        result = self._v._validate_cross_principle({"SRP": _pop(["Foo"]), "DRY": _empty()})
        self.assertIsNotNone(result)
        self.assertIn("DRY", result["principles_with_no_units"])

    def test_lsp_skip_detected(self):
        result = self._v._validate_cross_principle({"SRP": _pop(["Foo"]), "LSP": _empty()})
        self.assertIsNotNone(result)
        self.assertIn("LSP", result["principles_with_no_units"])

    def test_error_key_is_incomplete_submission(self):
        result = self._v._validate_cross_principle({"SRP": _pop(["Foo"]), "ISP": _empty()})
        self.assertEqual(result["error"], "incomplete_submission")


class TestUnitCoverageValidatorExpected(unittest.TestCase):
    def setUp(self):
        self._v = UnitCoverageValidator()

    def test_empty_expected_passes(self):
        result = self._v._validate_against_expected({"ISP": _empty()}, [])
        self.assertIsNone(result)

    def test_isp_empty_with_expected_units_rejected(self):
        result = self._v._validate_against_expected(
            {"SRP": _empty(), "ISP": _empty()},
            ["ProductCatalog"],
        )
        self.assertIsNotNone(result)
        self.assertIn("ISP", result["principles_with_no_units"])

    def test_all_populated_with_expected_passes(self):
        result = self._v._validate_against_expected(
            {"SRP": _pop(["Foo"]), "ISP": _pop(["Foo"])},
            ["Foo"],
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
