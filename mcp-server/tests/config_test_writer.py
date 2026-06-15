"""
solid-description: Writes configuration to a directory for test setup.
solid-category: unit-test
"""

from pathlib import Path

import yaml

from scoring.project_root_finder import CONFIG_DIR, CONFIG_BASENAME


class ConfigTestWriter:
    """Writes .solid-coder/severity-bands.yml files into a directory for testing config band overrides."""

    def write(self, directory: Path, content: dict) -> None:
        config_dir = directory / CONFIG_DIR
        config_dir.mkdir(exist_ok=True)
        (config_dir / CONFIG_BASENAME).write_text(
            yaml.dump(content), encoding="utf-8"
        )
