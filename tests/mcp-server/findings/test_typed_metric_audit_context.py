"""Verifies typed metric audit context at the MCP submission boundary."""

import unittest

from findings.mcp_batch_submission_builder import McpBatchSubmissionBuilder


"""
solid-name: TypedMetricAuditContextTests
solid-category: unit-test
solid-description: Verifies typed access to submitted metric exception decisions and evidence.
"""
class TypedMetricAuditContextTests(unittest.TestCase):
    def test_audit_fields_are_parsed_as_typed_attributes(self):
        payload = {
            "OCP": {
                "timestamp": "2026-08-13T00:00:00Z",
                "files": [{"units": [{
                    "unit_name": "Data",
                    "unit_kind": "class",
                    "metrics": {"OCP": {"sealed_variation_points": {
                        "value": 1,
                        "is_exception": True,
                        "additional_info": {
                            "reasoning": "This unit is a pure data structure.",
                            "evidence": "Data.swift:1-3 contains stored fields only.",
                        },
                    }}},
                }]}],
            }
        }

        submission = McpBatchSubmissionBuilder().build(payload)
        measurement = submission.principles[0].output.files[0].units[0].metrics[0].values[0]

        self.assertTrue(measurement.is_exception)
        self.assertEqual(
            measurement.additional_info.evidence,
            "Data.swift:1-3 contains stored fields only.",
        )


if __name__ == "__main__":
    unittest.main()
