"""
solid-name: TestFixtureDiscovery
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for FixtureDiscovery. Verifies convention-based fixture pairing,
missing-expectation error behavior, and sorted discovery order.
"""

import json
import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from fixture_discovery import FixtureDiscovery


def _make_fixture_tree(tmp: Path, fixtures: list[str], expectations: dict[str, dict]) -> None:
    (tmp / "fixtures").mkdir()
    (tmp / "expectations").mkdir()
    for name in fixtures:
        (tmp / "fixtures" / name).write_text("// fixture content", encoding="utf-8")
    for stem, data in expectations.items():
        (tmp / "expectations" / (stem + ".json")).write_text(
            json.dumps(data), encoding="utf-8"
        )


class TestFixtureDiscovery(unittest.TestCase):
    def test_discovers_fixture_pair_when_expectation_exists(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _make_fixture_tree(root, ["fixture-1.swift"], {"fixture-1": {"findings": []}})
            pairs = FixtureDiscovery().discover(root)
            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0].stem, "fixture-1")
            self.assertTrue(pairs[0].fixture_path.name.startswith("fixture-1"))
            self.assertEqual(pairs[0].expectation_path.name, "fixture-1.json")

    def test_raises_when_expectation_file_is_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _make_fixture_tree(root, ["fixture-2.swift"], {})
            with self.assertRaises(RuntimeError):
                FixtureDiscovery().discover(root)

    def test_discovers_multiple_fixtures_in_sorted_order(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _make_fixture_tree(
                root,
                ["fixture-2.swift", "fixture-1.swift"],
                {"fixture-1": {"findings": []}, "fixture-2": {"findings": []}},
            )
            pairs = FixtureDiscovery().discover(root)
            self.assertEqual([p.stem for p in pairs], ["fixture-1", "fixture-2"])


if __name__ == "__main__":
    unittest.main()
