"""
solid-name: OutputSchemaResolver
solid-category: service
solid-spec: [SPEC-027]
solid-description: Resolves external schema file references for step outputs.
"""

from __future__ import annotations

import os
from pathlib import Path

from harness.models import FlowValidationError
from harness.output_schema_resolving import OutputSchemaResolving
from scoring.yaml_config_file_loader import ConfigFileLoading


class OutputSchemaResolver(OutputSchemaResolving):

    def __init__(self, file_loader: ConfigFileLoading) -> None:
        self._file_loader = file_loader

    def resolve(self, step: dict, flow_file_path: str) -> dict:
        outputs = step.get("outputs")
        if not outputs:
            return step

        flow_dir = Path(os.path.abspath(flow_file_path)).parent
        resolved_outputs = [self._resolve_output(step, output, flow_dir) for output in outputs]

        resolved = dict(step)
        resolved["outputs"] = resolved_outputs
        return resolved

    def _resolve_output(self, step: dict, output: dict, flow_dir: Path) -> dict:
        schema_file = output.get("schema_file")
        if schema_file is None:
            return output

        if output.get("schema") is not None:
            raise FlowValidationError(
                f"Step '{step.get('id')}' output '{output.get('name')}' must declare at most one "
                f"of 'schema' or 'schema_file'"
            )

        schema = self._file_loader.load(flow_dir / schema_file)
        if schema is None:
            raise FlowValidationError(
                f"Step '{step.get('id')}' output '{output.get('name')}' schema_file not found "
                f"or not valid JSON: '{schema_file}'"
            )

        resolved = dict(output)
        resolved["schema"] = schema
        del resolved["schema_file"]
        return resolved
