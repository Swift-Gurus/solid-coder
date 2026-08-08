"""Parses JSON hook context into an immutable domain model."""

from pathlib import Path
from typing import Optional

from findings.hook_context import HookContext
from findings.hook_context_parsing import HookContextParsing
from health.llama.json_deserializer import JsonDeserializing


"""
solid-name: JsonHookContextParser
solid-category: boundary-adapter
solid-description: Validates decoded JSON fields and constructs immutable hook context.
"""
class JsonHookContextParser(HookContextParsing):
    def __init__(self, deserializer: JsonDeserializing) -> None:
        self._deserializer = deserializer

    def parse(self, raw_context: bytes) -> Optional[HookContext]:
        payload = self._deserializer.deserialize(raw_context)
        if payload is None:
            return None

        output_directory = payload.get("output_dir")
        file_path = payload.get("file_path")
        language = payload.get("language")
        expected_units = payload.get("expected_units")
        if (
            not isinstance(output_directory, str)
            or not output_directory
            or not isinstance(file_path, str)
            or not isinstance(language, str)
            or not isinstance(expected_units, list)
            or not all(isinstance(unit, str) for unit in expected_units)
        ):
            return None

        return HookContext(
            output_directory=Path(output_directory).resolve(),
            file_path=file_path,
            language=language,
            expected_units=tuple(expected_units),
        )
