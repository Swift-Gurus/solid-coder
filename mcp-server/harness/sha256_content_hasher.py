"""Produces SHA-256 audit hashes for authored byte content."""

import hashlib

from harness.content_hashing import ContentHashing


"""
solid-name: Sha256ContentHasher
solid-category: service
solid-spec: [SPEC-039]
solid-description: Produces stable SHA-256 hashes for authored byte content used in review audit snapshots.
"""
class Sha256ContentHasher(ContentHashing):
    def hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
