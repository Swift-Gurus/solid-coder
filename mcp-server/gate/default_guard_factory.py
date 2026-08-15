"""Constructs the production write-gate availability guard."""

import os

from api_key_guard import ApiKeyGuard
from composite_guard import CompositeGuard
from config_feature_toggle import ConfigFeatureToggle
from guard_checking import GuardChecking


"""
solid-name: DefaultGuardFactory
solid-category: factory
solid-description: Provides the production write-gate availability guard.
solid-tags: [hook]
"""
class DefaultGuardFactory:
    def create(self) -> GuardChecking:
        import hc_config as health_config

        return CompositeGuard([
            ConfigFeatureToggle(
                enabled_fn=lambda: health_config.load_config().code_review_on_write_enabled,
            ),
            ApiKeyGuard(
                backend_fn=lambda: health_config.load_config().llm.backend,
                api_key_fn=lambda: os.environ.get("ANTHROPIC_API_KEY", ""),
            ),
        ])
