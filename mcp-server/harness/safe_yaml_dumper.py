"""Adapts serializable values to PyYAML's safe dumping API."""

from __future__ import annotations

import yaml

from harness.yaml_dumping import YamlDumping


"""
solid-name: SafeYamlDumper
solid-category: adapter
solid-spec: [SPEC-031]
solid-description: Converts serializable values into safely formatted YAML text for configuration and data interchange.
"""
class SafeYamlDumper(YamlDumping):
    def dump(self, value: object) -> str:
        return yaml.safe_dump(
            value,
            default_flow_style=False,
            sort_keys=False,
        )
