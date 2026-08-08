"""
solid-description: Verifies each batch submission uses the health context in its requested output directory.
solid-category: unit-test
"""

import json
from pathlib import Path

from helpers import SubmitFindingsTestBase, make_schema_srp_partial


"""
solid-name: TestBatchSubmissionContextIsolation
solid-category: unit-test
solid-description: Verifies batch submissions cannot be redirected by another active health check.
"""
class TestBatchSubmissionContextIsolation(SubmitFindingsTestBase):
    def test_requested_output_dir_supplies_its_own_hook_context(self):
        output_dir = Path(self.tmp.name) / "health-request"
        output_dir.mkdir()
        expected_path = "/src/Expected.swift"
        (output_dir / "hook-input.json").write_text(
            json.dumps({
                "file_path": expected_path,
                "language": "Swift",
                "output_dir": str(output_dir),
                "expected_units": ["Foo"],
            }),
            encoding="utf-8",
        )

        self.handler.submit_batch_findings(
            str(output_dir),
            {"SRP": make_schema_srp_partial()},
        )

        result_path = output_dir / "SRP" / "review-output.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(result["files"][0]["file_path"], expected_path)
