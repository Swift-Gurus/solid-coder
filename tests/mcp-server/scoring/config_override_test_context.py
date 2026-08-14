"""Provides shared configuration-override scoring fixtures."""

from pathlib import Path

from band_value_extractor import BandValueExtractor
from config_bands_test_helper import ConfigBandsTestHelper
from config_test_writer import ConfigTestWriter
from metric_discoverer import MetricDiscoverer
from scoring.severity_scorer_factory import SeverityScorerFactory


"""
solid-name: ConfigOverrideTestContext
solid-category: unit-test
solid-description: Provides shared metric bands and scoring support for configuration-override tests.
"""
class ConfigOverrideTestContext:
    def __init__(self, references_root: Path) -> None:
        self.metrics = MetricDiscoverer(references_root).discover()
        self.extractor = BandValueExtractor()
        self.helper = ConfigBandsTestHelper(
            writer=ConfigTestWriter(),
            scorer_factory=SeverityScorerFactory().make,
        )
