"""Provides debug policy from effective project configuration."""

from typing import Protocol, runtime_checkable

from solid_coder_config_loader import SolidCoderConfigLoading


"""
solid-name: DebugModeReading
solid-category: abstraction
solid-description: Contract for determining whether debug mode requires retaining diagnostic artifacts.
"""
@runtime_checkable
class DebugModeReading(Protocol):
    def is_debug(self) -> bool: ...


"""
solid-name: HcConfigDebugReader
solid-category: service
solid-description: Determines debug retention policy from effective project configuration.
"""
class HcConfigDebugReader(DebugModeReading):
    def __init__(self, config_loader: SolidCoderConfigLoading) -> None:
        self._config_loader = config_loader

    def is_debug(self) -> bool:
        return self._config_loader.load().llm.debug
