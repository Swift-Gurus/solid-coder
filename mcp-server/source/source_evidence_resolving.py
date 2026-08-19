"""Defines source-evidence resolution from parser offsets."""

from typing import Protocol

from source.source_evidence import SourceEvidence


"""
solid-name: SourceEvidenceResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving auditable source evidence from a parsed fact and source offsets.
"""
class SourceEvidenceResolving(Protocol):

    def resolve(
        self,
        fact: str,
        source: str,
        start_offset: int,
        end_offset: int,
    ) -> SourceEvidence: ...
