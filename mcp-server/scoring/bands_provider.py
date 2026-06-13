"""
solid-description: Re-exports all band provider types for convenience.
solid-category: service
solid-tags: [utility, service]
"""

from scoring.band_evaluator import BandEvaluating, BandEvaluator  # noqa: F401
from scoring.config_path_collector import (  # noqa: F401
    ConfigCollecting, ConfigPathCollector,
    DirectoryWalking, DirectoryWalker,
    ConfigFileLoading, YamlConfigFileLoader,
    CONFIG_FILENAME,
)
from scoring.config_merger import ConfigMerging, ConfigMerger  # noqa: F401
from scoring.frontmatter_bands_provider import BandsProviding, FrontmatterBandsProvider  # noqa: F401
from scoring.config_bands_provider import ConfigBandsProvider  # noqa: F401


def make_config_bands_provider(
    rule_path_fn,
    project_root=None,
):
    """Wire production defaults: frontmatter → config chain → merged bands.

    Factory function — constructing and wiring concrete dependencies is this
    function's sole responsibility (OCP Factory exception).
    """
    return ConfigBandsProvider(
        base=FrontmatterBandsProvider(rule_path_fn=rule_path_fn),
        collector=ConfigPathCollector(
            walker=DirectoryWalker(),
            loader=YamlConfigFileLoader(),
        ),
        merger=ConfigMerger(),
        project_root=project_root,
    )
