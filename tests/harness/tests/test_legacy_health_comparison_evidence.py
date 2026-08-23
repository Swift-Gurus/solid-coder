"""Verifies legacy comparison evidence comes from its executed transcript."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
if str(_HARNESS) not in sys.path:
    sys.path.insert(0, str(_HARNESS))

from legacy_health_comparison_e2e_live_base import (  # noqa: E402
    LegacyHealthComparisonE2ELiveBase,
)


class TestLegacyHealthComparisonEvidence(unittest.TestCase):

    def test_hashes_the_exact_executed_health_prompt(self) -> None:
        review_prompt = (
            "# spawned-by: child\n\n"
            "You are a SOLID code quality gate doing a pre-write check.\n"
            "<detection-instructions>executed</detection-instructions>"
        )
        event = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": review_prompt}],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text(json.dumps(event) + "\n", encoding="utf-8")

            digest = LegacyHealthComparisonE2ELiveBase._instruction_hash(
                transcript
            )

        self.assertEqual(
            digest,
            hashlib.sha256(review_prompt.encode("utf-8")).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
