"""Loads health-check context directly from a requested output directory."""

from typing import Optional

from findings.hook_context import HookContext
from findings.hook_context_ownership_validating import HookContextOwnershipValidating
from findings.hook_context_path_resolving import HookContextPathResolving
from findings.hook_context_parsing import HookContextParsing
from findings.requested_hook_context_loading import RequestedHookContextLoading
from utils.prompt_builder import TextFileReading


"""
solid-name: RequestedHookContextLoader
solid-category: service
solid-description: Coordinates retrieval, decoding, and ownership validation of requested hook context.
"""
class RequestedHookContextLoader(RequestedHookContextLoading):
    def __init__(
        self,
        path_resolver: HookContextPathResolving,
        reader: TextFileReading,
        parser: HookContextParsing,
        ownership_validator: HookContextOwnershipValidating,
    ) -> None:
        self._path_resolver = path_resolver
        self._reader = reader
        self._parser = parser
        self._ownership_validator = ownership_validator

    def load(self, output_dir: str) -> Optional[HookContext]:
        raw_context = self._reader.read(self._path_resolver.resolve(output_dir))
        if raw_context is None:
            return None
        context = self._parser.parse(raw_context.encode("utf-8"))
        if context is None or not self._ownership_validator.is_owned(context, output_dir):
            return None
        return context
