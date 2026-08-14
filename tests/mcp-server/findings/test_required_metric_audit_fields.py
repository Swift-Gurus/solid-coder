"""Verifies required audit fields at the MCP submission boundary."""

import unittest

from pydantic import ValidationError

from findings.mcp_batch_submission_builder import McpBatchSubmissionBuilder


"""
solid-name: RequiredMetricAuditFieldsTests
solid-category: unit-test
solid-description: Verifies rejection of metric submissions missing required audit fields.
"""
class RequiredMetricAuditFieldsTests(unittest.TestCase):
    def test_missing_exception_and_audit_fields_are_rejected(self):
        payload = {
            "OCP": {
                "timestamp": "2026-08-13T00:00:00Z",
                "files": [{"units": [{
                    "unit_name": "Data",
                    "unit_kind": "class",
                    "metrics": {"OCP": {"sealed_variation_points": {"value": 1}}},
                }]}],
            }
        }

        with self.assertRaises(ValidationError) as raised:
            McpBatchSubmissionBuilder().build(payload)

        missing = {error["loc"][-1] for error in raised.exception.errors()}
        self.assertEqual(missing, {"is_exception", "additional_info"})


if __name__ == "__main__":
    unittest.main()
