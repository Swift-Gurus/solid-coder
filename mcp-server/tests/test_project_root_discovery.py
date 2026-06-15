"""
solid-description: Verifies that severity scoring configurations are correctly applied to files based on their project and directory context.
solid-category: unit-test
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scoring.severity_scorer import SeverityScorer
from tests.metric_discoverer import MetricDiscoverer
from tests.band_value_extractor import BandValueExtractor
from tests.config_test_writer import ConfigTestWriter
from tests.config_bands_test_helper import ConfigBandsTestHelper

REFS_ROOT = Path(__file__).resolve().parents[2] / "references"

_bands, _rule_path = MetricDiscoverer(REFS_ROOT).discover()[("SRP", "SRP-1", "verb_count")]
_EXTRACTOR = BandValueExtractor()
_HELPER = ConfigBandsTestHelper(writer=ConfigTestWriter(), scorer_factory=SeverityScorer.from_folder)


class TestProjectRootDiscovery(unittest.TestCase):
    """Validates .solid-coder/ directory detection and nested config scoping."""

    def test_nested_config_applies_only_to_files_in_subdirectory(self):
        """Child .solid-coder/severity-bands.yml disables a metric only for files within its directory."""
        severe_val = _EXTRACTOR.severe_value(_bands)
        scorer = SeverityScorer.from_folder(_rule_path.parent, project_root=None)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subdir = root / "src" / "tests"
            subdir.mkdir(parents=True)
            _HELPER.write_at(root, {})
            _HELPER.write_at(subdir, {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}})

            r_in = scorer.score_unit({"verb_count": severe_val}, "SRP-1", str(subdir / "FooTests.swift"))
            self.assertEqual(r_in["final_severity"], "COMPLIANT",
                             "Inside subdir: child config disables verb_count → COMPLIANT")

            r_out = scorer.score_unit({"verb_count": severe_val}, "SRP-1", str(root / "src" / "Foo.swift"))
            self.assertEqual(r_out["final_severity"], "SEVERE",
                             "Outside subdir: child config does not apply → SEVERE")

    def test_project_root_auto_detected_via_solid_coder_directory(self):
        """ProjectRootFinder auto-detects the root via .solid-coder/ marker — no project_root arg needed."""
        severe_val = _EXTRACTOR.severe_value(_bands)
        config = {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}}

        with tempfile.TemporaryDirectory() as tmp:
            src_file = Path(tmp) / "src" / "deep" / "Foo.swift"
            src_file.parent.mkdir(parents=True)
            _HELPER.write_at(Path(tmp), config)
            scorer = SeverityScorer.from_folder(_rule_path.parent, project_root=None)
            result = scorer.score_unit({"verb_count": severe_val}, "SRP-1", str(src_file))
            self.assertEqual(result["final_severity"], "COMPLIANT",
                             "Auto-detection: .solid-coder/ at project root found without project_root arg")

    def test_config_at_project_root_found_when_project_root_passed(self):
        """Passing project_root explicitly makes root .solid-coder/severity-bands.yml discoverable."""
        severe_val = _EXTRACTOR.severe_value(_bands)
        config = {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}}

        with tempfile.TemporaryDirectory() as tmp:
            src_file = Path(tmp) / "src" / "deep" / "Foo.swift"
            src_file.parent.mkdir(parents=True)
            _HELPER.write_at(Path(tmp), config)
            scorer = SeverityScorer.from_folder(_rule_path.parent, project_root=tmp)
            result = scorer.score_unit({"verb_count": severe_val}, "SRP-1", str(src_file))
            self.assertEqual(result["final_severity"], "COMPLIANT",
                             "With project_root set, root .solid-coder/severity-bands.yml is found → COMPLIANT")


if __name__ == "__main__":
    unittest.main()
