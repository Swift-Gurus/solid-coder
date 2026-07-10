"""
solid-name: ClaudeAgentTypeEnvDetector
solid-category: service
solid-spec: [SPEC-013]
solid-description: Detects the configured Claude agent type.
"""

from __future__ import annotations

import os

from harness.env_detecting import EnvDetecting


class ClaudeAgentTypeEnvDetector:

    def detect(self) -> str:
        return os.environ.get("CLAUDE_AGENT_TYPE", "")
