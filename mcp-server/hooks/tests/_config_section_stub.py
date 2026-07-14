"""
solid-description: Provides fixed configuration sections for testing.
solid-category: unit-test
"""

from unittest.mock import patch

import hc_config_schema


class ConfigSectionStub:
    """Context manager: patches read_llm_section/read_section to return fixed dicts."""

    def __init__(self, llm=None, hooks=None, inference=None, server=None):
        self._llm = llm or {}
        self._sections = {"hooks": hooks or {}, "inference": inference or {}, "server": server or {}}
        self._patcher = None

    def __enter__(self):
        self._patcher = patch.multiple(
            hc_config_schema,
            read_llm_section=lambda _cwd=None: self._llm,
            read_section=lambda name, _cwd=None: self._sections.get(name, {}),
        )
        self._patcher.start()
        return self

    def __exit__(self, *exc_info):
        self._patcher.stop()
        return False
