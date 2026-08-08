"""
solid-description: Writes configuration files to a directory to enable testing of configuration behavior.
solid-category: unit-test
"""

from pathlib import Path

import yaml

from scoring.project_root_finder import CONFIG_DIR, CONFIG_BASENAME, CONFIG_TOML


class ConfigTestWriter:
    """Writes .solid-coder/severity-bands.yml and a root-marker config.toml into a directory for testing config band overrides."""

    def write(self, directory: Path, content: dict) -> None:
        config_dir = directory / CONFIG_DIR
        config_dir.mkdir(exist_ok=True)
        marker = config_dir / CONFIG_TOML
        if not marker.exists():
            marker.touch()
        (config_dir / CONFIG_BASENAME).write_text(
            yaml.dump(content), encoding="utf-8"
        )