"""Verifies persistence of metric exception decisions and audit context."""

import json
from pathlib import Path

from helpers import SubmitFindingsTestBase, make_schema_srp_partial


"""
solid-name: MetricAuditPersistenceTests
solid-category: unit-test
solid-description: Verifies persisted review output retains submitted metric audit information.
"""
class MetricAuditPersistenceTests(SubmitFindingsTestBase):
    def test_persisted_measurement_retains_all_audit_fields(self):
        self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial()},
        )

        output = json.loads(
            Path(self.temp_path("SRP", "review-output.json")).read_text()
        )
        measurement = output["files"][0]["units"][0]["metrics"]["SRP"]["verb_count"]

        self.assertEqual(
            set(measurement),
            {"value", "is_exception", "additional_info"},
        )
        self.assertEqual(
            set(measurement["additional_info"]),
            {"reasoning", "evidence"},
        )
