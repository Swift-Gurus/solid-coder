"""Constructs the production write-gate exclusion checker."""

from exclusion_checking import ExclusionChecking
from gate_exclusion_checker import GateExclusionChecker


"""
solid-name: DefaultExclusionCheckerFactory
solid-category: factory
solid-description: Provides a configured write-gate exclusion checker.
solid-tags: [hook]
"""
class DefaultExclusionCheckerFactory:
    def create(self) -> ExclusionChecking:
        import hc_config as health_config
        from hook_utils import path_matches_pattern

        return GateExclusionChecker(
            exclude_patterns_fn=lambda: health_config.load_config().hook_exclude("pre_write_gate"),
            path_matcher_fn=path_matches_pattern,
        )
