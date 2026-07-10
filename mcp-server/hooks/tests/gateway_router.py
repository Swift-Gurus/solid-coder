"""
solid-description: Provides mock responses for gateway subprocess calls.
solid-category: unit-test
"""

from __future__ import annotations

import json
from typing import Protocol
from unittest.mock import MagicMock

_DETECTION_PRINCIPLES = [
    {
        "name": "srp",
        "content": "SRP detection rules",
        "principle_name": "SRP",
        "metrics_example": {},
    }
]


class GatewayRouting(Protocol):
    """
    solid-description: Contract for handling gateway subprocess calls.
    solid-category: abstraction
    """

    def handle(self, joined: str): ...


class GatewayRouter:
    """
    solid-description: Provides mock responses for gateway subprocess calls.
    solid-category: service
    """

    def __init__(self, health_dirs: list) -> None:
        self._health_dirs = iter(health_dirs)

    def handle(self, joined: str):
        if "get_candidate_tags" in joined:
            return MagicMock(returncode=0, stdout=json.dumps({"candidate_tags": ["srp"]}), stderr="")
        if "load_detection_rules" in joined:
            return MagicMock(returncode=0, stdout=json.dumps({"principles": _DETECTION_PRINCIPLES}), stderr="")
        if "get_output_path" in joined:
            return MagicMock(returncode=0, stdout=json.dumps({"output_root": str(next(self._health_dirs))}), stderr="")
        return MagicMock(returncode=0, stdout=json.dumps({}), stderr="")
