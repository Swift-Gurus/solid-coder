"""Decodes native cursor information into the shared semantic symbol model."""

from pathlib import Path

from pydantic import Field, FileUrl, field_validator
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol

"""
solid-name: NativeSourceKitCursorInfo
solid-category: model
solid-spec: [SPEC-064]
solid-description: Preserves native compiler symbol identity, declaration origin, SDK ownership, and structured return-type annotations.
"""


class NativeSourceKitCursorInfo(SourceKitSymbol):
    name: str | None = Field(default=None, validation_alias="key.name")
    symbol_id: str | None = Field(default=None, validation_alias="key.usr")
    is_system: bool | None = Field(default=None, validation_alias="key.is_system")
    declaration_uri: FileUrl | None = Field(
        default=None, validation_alias="key.filepath"
    )
    module_name: str | None = Field(default=None, validation_alias="key.modulename")
    annotated_declaration: str = Field(
        default="", validation_alias="key.fully_annotated_decl"
    )

    @field_validator("declaration_uri", mode="before")
    @classmethod
    def normalize_declaration_path(cls, value: str | FileUrl | None) -> FileUrl | None:
        if value is None or isinstance(value, FileUrl):
            return value
        return FileUrl(Path(value).as_uri())
