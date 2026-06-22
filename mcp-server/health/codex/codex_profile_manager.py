"""
solid-description: Generates and deploys a Codex configuration profile to the active environment.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import os
from pathlib import Path
from typing import Callable

from hook_utils import PLUGIN_ROOT as _DEFAULT_PLUGIN_ROOT

_PROFILE_NAME = "solid-coder-health"

_PROFILE_TEMPLATE = """\
# solid-coder health-check MCP profile — auto-generated, do not edit.

[mcp_servers.pipeline]
command = "python3"
args = ["{pipeline_server}"]

[mcp_servers.docs]
command = "python3"
args = ["{docs_server}"]

[[hooks.PreToolUse]]
matcher = "apply_patch"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "python3 {pre_write_gate}"

[[hooks.SessionStart]]
matcher = ""

[[hooks.SessionStart.hooks]]
type = "command"
command = "python3 {on_agent_start}"

[[hooks.Stop]]
matcher = ""

[[hooks.Stop.hooks]]
type = "command"
command = "python3 {on_agent_stop}"
"""


class CodexProfileManager:
    """Writes the solid-coder-health Codex profile into the active CODEX_HOME directory."""

    def __init__(
        self,
        codex_home: str = "",
        plugin_root: Path = _DEFAULT_PLUGIN_ROOT,
        home_resolver: Callable[[], str] = lambda: os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
    ) -> None:
        self._codex_home = codex_home or home_resolver()
        self._plugin_root = plugin_root

    def ensure_profile(self) -> str:
        """Write the profile file and return the profile name for use in CLI invocations."""
        home = Path(self._codex_home)
        home.mkdir(parents=True, exist_ok=True)
        hooks_dir = self._plugin_root / "hooks"
        (home / f"{_PROFILE_NAME}.config.toml").write_text(
            _PROFILE_TEMPLATE.format(
                pipeline_server=str(self._plugin_root / "mcp-server" / "pipeline" / "server.py"),
                docs_server=str(self._plugin_root / "mcp-server" / "docs" / "server.py"),
                pre_write_gate=str(hooks_dir / "pre_write_gate.py"),
                on_agent_start=str(hooks_dir / "on_agent_start.py"),
                on_agent_stop=str(hooks_dir / "on_agent_stop.py"),
            ),
            encoding="utf-8",
        )
        return _PROFILE_NAME