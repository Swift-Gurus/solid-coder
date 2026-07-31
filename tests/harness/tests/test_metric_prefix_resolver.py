"""
solid-name: test_metric_prefix_resolver
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Tests MetricPrefixResolver's extraction of a principle's metric-ID prefix from rule.md, including the folder-name-differs-from-prefix case (frontmatter -> FM).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from metric_prefix_resolver import MetricPrefixResolver  # noqa: E402


def _write_rule(tmp: Path, bands_block: str) -> Path:
    folder = tmp / "some-principle"
    folder.mkdir()
    (folder / "rule.md").write_text(
        f"---\nname: some-principle\nbands:\n{bands_block}\n---\n\n# Some Principle\n",
        encoding="utf-8",
    )
    return folder


class TestMetricPrefixResolver(unittest.TestCase):
    def test_prefix_matches_folder_name_case(self):
        with tempfile.TemporaryDirectory() as d:
            folder = _write_rule(Path(d), "  SRP-1:\n    verb_count:\n      severe:\n        greater_than: 3\n")
            self.assertEqual(MetricPrefixResolver().resolve(folder), "SRP")

    def test_prefix_differs_from_folder_name(self):
        """The exact bug this class fixes: folder is 'frontmatter', prefix is 'FM'."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / "frontmatter"
            folder.mkdir()
            (folder / "rule.md").write_text(
                "---\nname: frontmatter\nbands:\n"
                "  FM-1:\n    missing_frontmatter_count:\n      severe:\n        greater_than_or_equal: 1\n"
                "---\n\n# Frontmatter\n",
                encoding="utf-8",
            )
            self.assertEqual(MetricPrefixResolver().resolve(folder), "FM")

    def test_code_smells_folder_resolves_to_cs_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / "code-smells"
            folder.mkdir()
            (folder / "rule.md").write_text(
                "---\nname: code-smells\nbands:\n"
                "  CS-1:\n    static_logic_count:\n      severe:\n        greater_than_or_equal: 1\n"
                "---\n\n# Code Smells\n",
                encoding="utf-8",
            )
            self.assertEqual(MetricPrefixResolver().resolve(folder), "CS")

    def test_missing_bands_raises(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "empty-principle"
            folder.mkdir()
            (folder / "rule.md").write_text("---\nname: empty-principle\n---\n\n# Empty\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                MetricPrefixResolver().resolve(folder)


if __name__ == "__main__":
    unittest.main()
