"""Constructs the production write-gate exclusion checker."""

from pathlib import Path
from typing import Protocol

from gate.gate_exclusion_checker import GateExclusionChecker
from utils.patterns.fnmatch_pattern_matcher import FnmatchPatternMatcher
from utils.patterns.path_pattern_matcher import PathPatternMatcher


"""
solid-name: ExclusionPolicyCreating
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for creating an exclusion policy from the effective configuration of a requested project.
"""
class ExclusionPolicyCreating(Protocol):
    def create(self, project_root: Path | None = None) -> GateExclusionChecker: ...


"""
solid-name: DefaultExclusionCheckerFactory
solid-category: factory
solid-description: Provides a configured write-gate exclusion checker.
solid-tags: [hook]
"""
class DefaultExclusionCheckerFactory(ExclusionPolicyCreating):
    def create(self, project_root: Path | None = None) -> GateExclusionChecker:
        if project_root is None:
            import hc_config as health_config

            config = health_config.SolidCoderConfigLoader().load()
        else:
            from health.config.solid_coder_config_loader import SolidCoderConfigLoader

            config = SolidCoderConfigLoader().load(cwd=project_root)

        return GateExclusionChecker(
            patterns=config.hook_exclude("pre_write_gate"),
            matcher=PathPatternMatcher(FnmatchPatternMatcher()),
        )
