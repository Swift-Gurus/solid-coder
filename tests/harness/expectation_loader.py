"""
solid-name: ExpectationLoader
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Loads an expectation JSON file and returns an Expectation dataclass. An empty
findings list signals a compliant-fixture expectation. Exits with code 1 on missing or malformed
JSON — naming the failing path in the error message.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import ExpectationLoading  # noqa: E402
from models import Expectation, ExpectedFinding  # noqa: E402


class ExpectationLoader(ExpectationLoading):
    def load(self, expectation_path: Path) -> Expectation:
        if not expectation_path.exists():
            raise RuntimeError(f"Expectation file not found: {expectation_path}")
        try:
            raw = json.loads(expectation_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Malformed JSON in expectation file {expectation_path}: {exc}"
            ) from exc
        findings = [
            ExpectedFinding(
                unit_name=entry["unit_name"],
                metric_id=entry["metric_id"],
                severity=entry["severity"],
                metrics=entry.get("metrics"),
            )
            for entry in raw.get("findings", [])
        ]
        return Expectation(findings=findings)
