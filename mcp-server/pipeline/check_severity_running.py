"""Defines severe-findings evaluation for pipeline tools."""

from typing import Protocol


"""
solid-name: CheckSeverityRunning
solid-category: abstraction
solid-description: Contract for evaluating review outputs for severe findings.
"""
class CheckSeverityRunning(Protocol):
    def check_severity(self, output_root: str) -> dict: ...
