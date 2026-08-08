import sys
from pathlib import Path
_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from pathlib import Path

from codex_config_argument_building import CodexConfigArgumentBuilding


"""
solid-name: CodexCommandBuilder
solid-category: service
solid-description: Constructs configurable Codex execution commands.
"""
class CodexCommandBuilder:
    """Builds the codex exec command list for a health-check session."""

    def __init__(
        self,
        model: str,
        mcp_config: str,
        config_argument_builder: CodexConfigArgumentBuilding,
    ) -> None:
        self._model = model
        self._mcp_config = mcp_config
        self._config_argument_builder = config_argument_builder

    def build(self, result_path: Path) -> list:
        """Return the codex exec command, parameterized by output file path."""
        cmd = [
            "codex", "exec",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-bypass-hook-trust",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--output-last-message", str(result_path),
            "-",
        ]
        cmd += self._config_argument_builder.build(self._mcp_config)
        if self._model:
            cmd += ["--model", self._model]
        return cmd
