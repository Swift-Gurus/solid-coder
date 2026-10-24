"""
solid-description: Blocks releases whose packaged plugin cannot serve MCP or enforce deterministic hook denials using the Desktop Python outside the development environment.
solid-category: utility
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PACKAGE_PATHS = (
    ".claude-plugin",
    ".codex-plugin",
    ".mcp.json",
    "agents",
    "hooks",
    "mcp-server",
    "references",
    "requirements-runtime.txt",
    "skills",
    "spec-driven-development",
    "workflows",
)


def copy_package(root: Path, destination: Path) -> None:
    for relative in PACKAGE_PATHS:
        source, target = root / relative, destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv"),
            )
        else:
            shutil.copy2(source, target)


def clean_environment(
    home: Path, host_bin: Path, plugin: Path, project: Path
) -> dict[str, str]:
    environment = {
        "HOME": str(home),
        "PATH": f"{host_bin}:/usr/bin:/bin",
        "XDG_CACHE_HOME": str(home / ".cache"),
        "CLAUDE_PLUGIN_ROOT": str(plugin),
        "PLUGIN_ROOT": str(plugin),
        "CLAUDE_PROJECT_DIR": str(project),
        "PYTHONNOUSERSITE": "1",
    }
    for key in (
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "https_proxy",
        "http_proxy",
        "all_proxy",
        "no_proxy",
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
        "PIP_CERT",
        "PIP_INDEX_URL",
        "PIP_EXTRA_INDEX_URL",
        "PIP_FIND_LINKS",
        "PIP_NO_INDEX",
    ):
        if key in os.environ:
            environment[key] = os.environ[key]
    return environment


def run_process(
    command: list[str], payload: str, project: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=payload,
        cwd=project,
        env=environment,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )


def check_mcp(
    server: dict[str, Any], plugin: Path, project: Path, environment: dict[str, str]
) -> None:
    arguments = []
    for argument in server["args"]:
        expanded = argument.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin))
        if not expanded.startswith("-") and (plugin / expanded).is_file():
            expanded = str(plugin / expanded)
        arguments.append(expanded)
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    result = run_process(
        [server["command"], *arguments],
        "".join(json.dumps(message) + "\n" for message in messages),
        project,
        environment,
    )
    if result.returncode:
        raise RuntimeError(f"MCP exited {result.returncode}: {result.stderr}")
    responses = [
        json.loads(line) for line in result.stdout.splitlines() if line.strip()
    ]
    if (
        [response.get("id") for response in responses] != [1, 2]
        or not responses[0].get("result", {}).get("protocolVersion")
        or not responses[1].get("result", {}).get("tools")
    ):
        raise ValueError(
            f"Invalid MCP initialize/tools/list responses: {result.stdout}"
        )


def check_hook(
    command: str, project: Path, environment: dict[str, str], *, invalid_config: bool
) -> None:
    config = project / ".solid-coder" / "config.toml"
    if invalid_config:
        config.parent.mkdir(exist_ok=True)
        config.write_text('code_review_on_write_enabled = "not-a-boolean"\n')
    try:
        result = run_process(
            ["/bin/sh", "-c", command],
            json.dumps(
                {
                    "tool_name": "Read",
                    "tool_input": {},
                    "cwd": str(project),
                    "session_id": "release-smoke",
                }
            ),
            project,
            environment,
        )
    finally:
        if invalid_config:
            config.unlink()
    if not invalid_config:
        if result.returncode:
            raise RuntimeError(f"Hook startup failed: {result.stderr}\n{result.stdout}")
        if result.stdout.strip():
            json.loads(result.stdout)
        return
    denied = result.returncode == 2
    if result.stdout.strip():
        output = json.loads(result.stdout)
        denied = (
            denied
            or output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
            or output.get("decision") == "block"
        )
    if not denied or "config" not in (result.stdout + result.stderr).lower():
        raise RuntimeError(
            f"Hook did not deny invalid config: {result.returncode}\n{result.stdout}\n{result.stderr}"
        )


def smoke(root: Path, interpreter: Path) -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="solid-coder release ") as directory:
        scratch = Path(directory)
        plugin, project, home = [
            scratch / name for name in ("installed plugin", "unrelated project", "home")
        ]
        for path in (plugin, project, home):
            path.mkdir()
        copy_package(root, plugin)
        environment = clean_environment(
            home, interpreter.absolute().parent, plugin, project
        )
        selected = shutil.which("python3.12", path=environment["PATH"])
        if selected is None or Path(selected).resolve() != interpreter.resolve():
            raise ValueError(
                "Selected Desktop interpreter must provide python3.12 in its bin directory"
            )
        print(f"Desktop Python: {selected}", flush=True)
        claude = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
        if claude["version"] != codex["version"]:
            raise ValueError("Claude and Codex manifest versions disagree")
        checkout = json.loads((plugin / codex["mcpServers"]).read_text())
        if set(claude["mcpServers"]) != {
            "apple-build",
            "docs",
            "flow-engine",
            "pipeline",
        }:
            raise ValueError(
                "Claude manifest must configure all four supported MCP servers"
            )
        if set(checkout["mcpServers"]) != {
            f"solid-coder-{name}" for name in claude["mcpServers"]
        }:
            raise ValueError(
                "Codex manifest must configure all four supported MCP servers"
            )
        checks: list[tuple[str, dict[str, Any]]] = [
            (f"{host}/{name}", server)
            for host, servers in (
                ("claude", claude["mcpServers"]),
                ("codex", checkout["mcpServers"]),
            )
            for name, server in servers.items()
        ]
        for name, server in checks:
            try:
                check_mcp(server, plugin, project, environment)
                print(f"PASS {name}", flush=True)
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
            ) as error:
                failures.append(f"{name}: {error}")
                return failures
        hooks = json.loads((plugin / "hooks/hooks.json").read_text())
        commands = [
            hook["command"]
            for entries in hooks["hooks"].values()
            for entry in entries
            for hook in entry["hooks"]
        ]
        command = next(
            command for command in commands if "pre_write_gate.py" in command
        )
        for startup in commands:
            name = startup.rsplit("/", 1)[-1]
            try:
                check_hook(startup, project, environment, invalid_config=False)
                print(f"PASS hook startup {name}", flush=True)
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
            ) as error:
                failures.append(f"{name}: {error}")
        try:
            check_hook(command, project, environment, invalid_config=True)
            print("PASS write gate invalid-config denial", flush=True)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            failures.append(f"write gate invalid-config denial: {error}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(os.environ.get("DESKTOP_PYTHON", sys._base_executable)),
        help="Desktop's Python 3.12 executable; defaults to base Python, never the active virtualenv",
    )
    options = parser.parse_args()
    try:
        failures = smoke(options.plugin_root.resolve(), options.python.absolute())
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        StopIteration,
        subprocess.SubprocessError,
    ) as error:
        print(f"Release smoke failed: {error}", file=sys.stderr)
        return 1
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print(
        "Release smoke passed: copied package, Desktop Python, both hosts, all hook startups and config-error denial"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
