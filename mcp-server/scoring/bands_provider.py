"""
solid-description: Factory for creating band providers that merge scoring bands from multiple sources.
solid-category: service
solid-tags: [utility, service]
"""

from collections.abc import Callable

from gate_logger import GateLogger
from utils.debug_logger import DebugLogger

from scoring.band_evaluator import BandEvaluating, BandEvaluator  # noqa: F401
from scoring.config_bands_provider import ConfigBandsProvider
from scoring.config_merger import ConfigMerger, ConfigMerging  # noqa: F401
from scoring.config_path_collector import ConfigCollecting, ConfigPathCollector  # noqa: F401
from scoring.directory_walker import DirectoryWalker, DirectoryWalking  # noqa: F401
from scoring.frontmatter_bands_provider import BandsProviding, FrontmatterBandsProvider  # noqa: F401
from scoring.parent_chain import ParentChaining, parent_chain  # noqa: F401
from scoring.project_root_finder import (  # noqa: F401
    CONFIG_BASENAME,
    CONFIG_DIR,
    ProjectRootFinder,
    ProjectRootFinding,
)
from scoring.yaml_config_file_loader import ConfigFileLoading, YamlConfigFileLoader  # noqa: F401
from scoring.yaml_loader import PyYamlLoader, YamlLoading  # noqa: F401


class ConfigBandsProviderFactory:
    """Wires production defaults and creates a ConfigBandsProvider.

    Factory class — constructing and wiring concrete dependencies is this
    class's sole responsibility (OCP Factory exception).
    """

    def __init__(
        self,
        rule_path_fn: Callable,
        project_root: str | None = None,
    ) -> None:
        self._rule_path_fn = rule_path_fn
        self._project_root = project_root

    def create(self) -> ConfigBandsProvider:
        return ConfigBandsProvider(
            base=FrontmatterBandsProvider(rule_path_fn=self._rule_path_fn),
            collector=ConfigPathCollector(
                walker=DirectoryWalker(chainer=parent_chain),
                loader=YamlConfigFileLoader(
                    loader=PyYamlLoader(), logger=GateLogger(DebugLogger())
                ),
                root_finder=ProjectRootFinder(),
            ),
            merger=ConfigMerger(),
            project_root=self._project_root,
        )


def make_config_bands_provider(
    rule_path_fn,
    project_root=None,
):
    """Backward-compatible shim — delegates to ConfigBandsProviderFactory."""
    return ConfigBandsProviderFactory(
        rule_path_fn=rule_path_fn, project_root=project_root
    ).create()
