"""Runs the locked legacy health smoke scenario through Codex Terra."""

from legacy_health_comparison_e2e_live_base import (
    LegacyHealthComparisonE2ELiveBase,
)


"""
solid-name: TestCodexLegacyHealthComparisonLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Proves the legacy health comparison path completes under the pinned Codex Terra profile before repeated measurement.
"""
class TestCodexLegacyHealthComparisonLive(
    LegacyHealthComparisonE2ELiveBase,
):
    __test__ = True
