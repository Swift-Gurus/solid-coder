"""
solid-name: FixtureDiscovery
solid-category: service
solid-spec: [SPEC-014]
solid-description: Convention-based fixture discovery for the principle test harness. Globs
fixtures/fixture-* from the given tests path, pairs each with expectations/<stem>.json, and
exits with code 1 (naming the missing path) when a pairing is impossible.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import FixtureDiscovering  # noqa: E402
from models import FixturePair  # noqa: E402


class FixtureDiscovery(FixtureDiscovering):
    def discover(self, tests_path: Path) -> list[FixturePair]:
        fixtures_dir = tests_path / "fixtures"
        expectations_dir = tests_path / "expectations"
        raw = sorted(fixtures_dir.glob("fixture-*"), key=lambda p: p.name)
        pairs: list[FixturePair] = []
        for fixture_path in raw:
            stem = fixture_path.stem
            expectation_path = expectations_dir / (stem + ".json")
            if not expectation_path.exists():
                raise RuntimeError(f"Missing expectation file: {expectation_path}")
            pairs.append(
                FixturePair(
                    fixture_path=fixture_path,
                    expectation_path=expectation_path,
                    stem=stem,
                )
            )
        return pairs
