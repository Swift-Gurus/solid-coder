"""
solid-name: TestUnitCoverageAppliesTo
solid-category: unit-test
solid-description: Verifies selective enforcement of principle requirements on different unit types.
"""

import unittest
from findings.unit_coverage_validator import UnitCoverageValidator

_APPLIES_TO = {"isp": ["protocol"]}


def _payload(units_with_kinds: list) -> dict:
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "files": [{"file_path": "/F.swift", "units": [
            {"unit_name": n, "unit_kind": k, "metrics": {}}
            for n, k in units_with_kinds
        ]}],
    }


def _empty() -> dict:
    return {"timestamp": "2026-01-01T00:00:00Z", "files": [{"units": []}]}


class TestUnitCoverageAppliesTo(unittest.TestCase):
    def setUp(self):
        self._v = UnitCoverageValidator(applies_to=_APPLIES_TO)

    # --- cross-principle ---

    def test_isp_empty_classes_only_passes(self):
        result = self._v._validate_cross_principle({
            "srp": _payload([("Foo", "class"), ("Bar", "class")]),
            "isp": _empty(),
        })
        self.assertIsNone(result)

    def test_isp_empty_function_only_passes(self):
        result = self._v._validate_cross_principle({
            "srp": _payload([("_helper", "function")]),
            "isp": _empty(),
        })
        self.assertIsNone(result)

    def test_isp_empty_protocol_present_rejected(self):
        result = self._v._validate_cross_principle({
            "srp": _payload([("MyProtocol", "protocol")]),
            "isp": _empty(),
        })
        self.assertIsNotNone(result)
        self.assertIn("isp", result["principles_with_no_units"])

    def test_isp_empty_mixed_with_protocol_rejected(self):
        result = self._v._validate_cross_principle({
            "srp": _payload([("Foo", "class"), ("Proto", "protocol")]),
            "isp": _empty(),
        })
        self.assertIsNotNone(result)

    def test_unrestricted_principle_still_required(self):
        result = self._v._validate_cross_principle({
            "srp": _payload([("Foo", "class")]),
            "dry": _empty(),
        })
        self.assertIsNotNone(result)
        self.assertIn("dry", result["principles_with_no_units"])

    def test_no_applies_to_preserves_original_behaviour(self):
        v = UnitCoverageValidator()
        result = v._validate_cross_principle({
            "srp": _payload([("Foo", "class")]),
            "isp": _empty(),
        })
        self.assertIsNotNone(result)

    # --- validate_against_expected ---

    def test_isp_empty_expected_are_classes_passes(self):
        result = self._v._validate_against_expected(
            {
                "srp": _payload([("Foo", "class"), ("Bar", "class")]),
                "isp": _empty(),
            },
            expected=["Foo", "Bar"],
        )
        self.assertIsNone(result)

    def test_isp_empty_expected_includes_protocol_rejected(self):
        result = self._v._validate_against_expected(
            {
                "srp": _payload([("MyProto", "protocol")]),
                "isp": _empty(),
            },
            expected=["MyProto"],
        )
        self.assertIsNotNone(result)
        self.assertIn("isp", result["principles_with_no_units"])


if __name__ == "__main__":
    unittest.main()
