"""
solid-name: OsEnvReader
solid-category: service
solid-spec: [SPEC-013]
solid-description: Provides environment variable lookup with optional default values.
"""

from __future__ import annotations

import os

from harness.env_reading import EnvReading


class OsEnvReader:

    def get(self, key: str, default: str = "") -> str:
        return os.environ.get(key, default)
