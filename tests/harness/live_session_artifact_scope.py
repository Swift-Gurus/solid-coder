"""Defines the domain and scenario hierarchy for one live-test evidence bundle."""

from dataclasses import dataclass


"""
solid-name: LiveSessionArtifactScope
solid-category: value
solid-description: Identifies the domain and scenario folders that own one live integration session's artifacts.
"""
@dataclass(frozen=True)
class LiveSessionArtifactScope:
    domain: str
    scenario: str
