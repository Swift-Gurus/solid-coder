"""Defines supported Git working-tree change kinds."""

from enum import Enum


"""
solid-name: SourceChangeKind
solid-category: model
solid-spec: [SPEC-040]
solid-description: Enumerates normalized source-file change kinds reported from Git.
"""
class SourceChangeKind(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
