"""Validated project extensions to the bundled metadata vocabulary."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


"""
solid-name: FrontmatterConfig
solid-category: model
solid-spec: [SPEC-069]
solid-description: Validates project additions to the source metadata category vocabulary.
"""
class FrontmatterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    additional_categories: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_categories(self) -> Self:
        for value in self.additional_categories:
            if (value in {"misc", "other", "stuff", "todo"}
                    or not value.isascii()
                    or any(not part or not part.isalpha() or not part.islower()
                           for part in value.split("-"))):
                raise ValueError("Categories must be meaningful lowercase hyphenated names, not placeholders")
        return self
