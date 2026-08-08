"""Validates the public contract of package entrypoints."""

from __future__ import annotations

import re
from pathlib import Path

from harness.models import FlowValidationError

_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[-/][a-z0-9]+)*$")


"""
solid-name: WorkflowPackageValidator
solid-category: service
solid-spec: [SPEC-035]
solid-description: Validates workflow package IDs, labels, turn limits, and step availability.
"""
class WorkflowPackageValidator:
    def validate(self, path: Path, raw: dict | None) -> None:
        if raw is None:
            raise FlowValidationError(f"Workflow package entrypoint is not valid YAML: '{path}'")
        workflow_id = raw.get("id")
        if not isinstance(workflow_id, str) or not _ID_PATTERN.fullmatch(workflow_id):
            raise FlowValidationError(
                f"Workflow package '{path}' must declare an id matching '{_ID_PATTERN.pattern}'"
            )
        if not isinstance(raw.get("name"), str) or not raw["name"].strip():
            raise FlowValidationError(f"Workflow package '{workflow_id}' must declare a non-empty name")
        max_turns = raw.get("max_turns")
        if not isinstance(max_turns, int) or isinstance(max_turns, bool) or max_turns < 1:
            raise FlowValidationError(f"Workflow package '{workflow_id}' must declare max_turns >= 1")
        if not isinstance(raw.get("steps"), list) or not raw["steps"]:
            raise FlowValidationError(f"Workflow package '{workflow_id}' must declare a non-empty steps list")
