"""Defines workflow iteration declaration decoding."""

from typing import Protocol

from harness.for_each_declaration import ForEachDeclaration


"""
solid-name: ForEachDeclarationParsing
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for decoding authored or snapshotted iteration declarations into their typed runtime form.
"""
class ForEachDeclarationParsing(Protocol):
    def parse(
        self,
        step_id: str,
        raw: object,
    ) -> ForEachDeclaration: ...
