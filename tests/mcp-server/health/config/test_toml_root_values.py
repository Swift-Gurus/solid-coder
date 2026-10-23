"""Checks the TOML root-value decoding boundary."""

import sys
from datetime import date, datetime, time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "mcp-server" / "health" / "config"))

from toml_root_values import TomlRootValues

"""
solid-name: TestTomlRootValues
solid-category: unit-test
solid-description: Verifies TOML root values remain available for validation while named tables are excluded.
"""


class TestTomlRootValues:
    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            42,
            1.25,
            "legacy",
            None,
            [],
            ["swift", "python"],
            [{"name": "example"}],
            date(2026, 10, 2),
            datetime(2026, 10, 2, 12, 30),
            time(12, 30),
        ],
    )
    def test_preserves_non_table_values_and_excludes_named_tables(self, value):
        document = {
            "unknown_root_key": value,
            "llm": {"backend": "codex"},
            "feature_flags": {"health_check_mode": "legacy"},
        }

        result = TomlRootValues.model_validate(document).model_dump()

        assert result == {"unknown_root_key": value}
