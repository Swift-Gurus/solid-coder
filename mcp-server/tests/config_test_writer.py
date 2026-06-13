"""
solid-description: Writes .solid-coder.yml config files into a directory for use in config bands tests.
solid-category: unit-test
"""

from pathlib import Path

import yaml

CONFIG_FILENAME = ".solid-coder.yml"


class ConfigTestWriter:
    """Writes .solid-coder.yml files into a directory for testing config band overrides."""

    def write(self, directory: Path, content: dict) -> None:
        (directory / CONFIG_FILENAME).write_text(
            yaml.dump(content), encoding="utf-8"
        )
