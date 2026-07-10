"""
solid-description: Infrastructure enabling runner strategies to apply environment configuration.
solid-category: service
solid-tags: [hook]
"""

import os
from typing import Protocol


class EnvironmentWriting(Protocol):
    def set(self, key: str, value: str) -> None: ...


class OSEnvironmentWriter:
    """Boundary adapter: wraps os.environ mutation for injection."""

    def set(self, key: str, value: str) -> None:
        os.environ[key] = value


class RunnerStrategyBase:
    """Shared session-type constant and environment setup for all runner strategies."""

    session_type: str = "health_check"
    _env_writer: EnvironmentWriting = OSEnvironmentWriter()

    def apply_env(self) -> None:
        self._env_writer.set("SOLID_CODER_SESSION_TYPE", self.session_type)
