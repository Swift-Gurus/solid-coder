"""Defines the sealed source-file change variants."""

from typing import Annotated, Union

from pydantic import Field

from source.added_source_file_change import AddedSourceFileChange
from source.deleted_source_file_change import DeletedSourceFileChange
from source.modified_source_file_change import ModifiedSourceFileChange
from source.renamed_source_file_change import RenamedSourceFileChange


SourceFileChange = Annotated[
    Union[
        AddedSourceFileChange,
        ModifiedSourceFileChange,
        DeletedSourceFileChange,
        RenamedSourceFileChange,
    ],
    Field(discriminator="kind"),
]
