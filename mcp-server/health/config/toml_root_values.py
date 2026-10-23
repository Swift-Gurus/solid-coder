"""Separates non-table TOML values at the configuration decoding boundary."""

from datetime import date, datetime, time

from pydantic import (
    OnErrorOmit,
    RootModel,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
)

"""
solid-name: TomlRootValues
solid-category: model
solid-description: Preserves root configuration values while excluding named TOML tables from scalar configuration validation.
"""


class TomlRootValues(
    RootModel[
        dict[
            str,
            OnErrorOmit[
                StrictBool
                | StrictInt
                | StrictFloat
                | StrictStr
                | datetime
                | date
                | time
                | list[object]
                | None
            ],
        ]
    ]
):
    pass
