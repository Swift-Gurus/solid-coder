"""Provides shared project-root scoring fixtures."""

from __future__ import annotations

from pathlib import Path

from band_value_extractor import BandValueExtractor
from config_bands_test_helper import ConfigBandsTestHelper
from config_test_writer import ConfigTestWriter
from metric_discoverer import MetricDiscoverer
from scoring.severity_scorer_factory import SeverityScorerFactory


"""
solid-name: ProjectRootTestContext
solid-category: unit-test
solid-description: Provides shared SRP bands and scoring support for project-root discovery tests.
"""
class ProjectRootTestContext:
    def __init__(self, references_root: Path) -> None:
        self.bands, self.rule_path = MetricDiscoverer(references_root).discover()[
            ("SRP", "SRP-1", "verb_count")
        ]
        self.severe_value = BandValueExtractor().severe_value(self.bands)
        self.helper = ConfigBandsTestHelper(
            writer=ConfigTestWriter(),
            scorer_factory=SeverityScorerFactory().make,
        )

    def make_scorer(self, project_root: str | None = None):
        return SeverityScorerFactory(project_root=project_root).make(
            self.rule_path.parent
        )
