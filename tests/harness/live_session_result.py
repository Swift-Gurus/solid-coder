"""Defines the observable result of one live integration session."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: LiveSessionResult
solid-category: value
solid-description: Carries the child session identity and final model output returned by a live backend adapter.
"""
@dataclass(frozen=True)
class LiveSessionResult:

    session_id: str
    final_output: str
