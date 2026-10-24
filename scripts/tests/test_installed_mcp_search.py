"""Exercises installed search with real session context and repository boundaries."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "release_smoke", Path(__file__).resolve().parents[1] / "release-smoke.py"
)
assert SPEC is not None and SPEC.loader is not None
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


@pytest.fixture
def installed_search(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    plugin = tmp_path / "installed plugin"
    SMOKE.copy_package(Path(__file__).resolve().parents[2], plugin)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "init", "-q", str(plugin)], check=True
    )
    home = tmp_path / "home"
    home.mkdir()
    first, second = tmp_path / "first project", tmp_path / "second project"
    environment = SMOKE.clean_environment(
        home, Path(sys._base_executable).parent, plugin, first
    )
    environment.pop("CLAUDE_PROJECT_DIR")
    for root, session_id, name in (
        (first, "first-session", "FirstProjectSentinel"),
        (second, "second-session", "SecondProjectSentinel"),
    ):
        sources = root / "Sources"
        sources.mkdir(parents=True)
        subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "init", "-q", str(root)],
            check=True,
        )
        (sources / f"{name}.swift").write_text(
            f"struct {name} {{}}\n", encoding="utf-8"
        )
        registered = SMOKE.run_process(
            [sys._base_executable, str(plugin / "mcp-server/hooks/on_agent_start.py")],
            json.dumps({"session_id": session_id, "cwd": str(sources)}),
            plugin,
            environment,
        )
        assert registered.returncode == 0, registered.stderr
        recorded = home / ".solid-coder/sessions" / session_id / "project-root"
        assert recorded.read_text().strip() == str(sources.resolve())
    return plugin, first.resolve(), second.resolve(), environment


def search_calls(
    installation: tuple[Path, Path, Path, dict[str, str]],
    calls: list[tuple[str, str | None, str]],
    metadata_key: str = "threadId",
) -> list[str]:
    plugin, _, _, environment = installation
    messages: list[dict] = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    ]
    for request_id, (session_id, sources_dir, term) in enumerate(calls, 2):
        metadata = (
            {"threadId": session_id}
            if metadata_key == "threadId"
            else {"x-codex-turn-metadata": {"session_id": session_id}}
        )
        arguments: dict = {"query": term, "min_matches": 1}
        if sources_dir is not None:
            arguments["sources_dir"] = sources_dir
        messages.append(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "search_codebase",
                    "arguments": arguments,
                    "_meta": metadata,
                },
            }
        )
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    servers = json.loads((plugin / manifest["mcpServers"]).read_text())
    server = servers["mcpServers"]["solid-coder-pipeline"]
    result = SMOKE.run_process(
        [server["command"], *server["args"]],
        "".join(json.dumps(message) + "\n" for message in messages),
        plugin / server.get("cwd", "."),
        environment,
    )
    assert result.returncode == 0, result.stderr
    responses = [
        json.loads(line) for line in result.stdout.splitlines() if line.strip()
    ]
    assert [response["id"] for response in responses] == list(range(1, len(calls) + 2))
    return [
        "\n".join(
            item["text"]
            for item in response["result"]["content"]
            if item["type"] == "text"
        )
        for response in responses[1:]
    ]


@pytest.mark.parametrize("metadata_key", ["threadId", "x-codex-turn-metadata"])
def test_installed_search_uses_each_request_session_instead_of_plugin_cwd(
    installed_search, metadata_key
):
    _, first, second, _ = installed_search

    results = search_calls(
        installed_search,
        [
            ("first-session", str(first), "FirstProjectSentinel"),
            ("second-session", str(second), "SecondProjectSentinel"),
            ("first-session", "Sources", "FirstProjectSentinel"),
            ("second-session", None, "SecondProjectSentinel"),
        ],
        metadata_key,
    )

    assert str(first / "Sources/FirstProjectSentinel.swift") in results[0]
    assert str(second / "Sources/SecondProjectSentinel.swift") in results[1]
    assert str(first / "Sources/FirstProjectSentinel.swift") in results[2]
    assert str(second / "Sources/SecondProjectSentinel.swift") in results[3]


@pytest.mark.parametrize("escape", ["absolute", "parent", "symlink"])
def test_installed_search_rejects_targets_outside_the_session_repository(
    installed_search, escape
):
    _, first, second, _ = installed_search
    (first / "escape").symlink_to(second, target_is_directory=True)
    target = {
        "absolute": str(second),
        "parent": "../second project",
        "symlink": "escape",
    }[escape]

    result = search_calls(
        installed_search, [("first-session", target, "SecondProjectSentinel")]
    )[0]

    assert "outside repository" in result
    assert f"repository '{first}'" in result
    assert "candidate_id:" not in result


def test_installed_search_rejects_outside_symlink_discovered_during_search(
    installed_search,
):
    _, first, second, _ = installed_search
    (first / "Sources/Escaped.swift").symlink_to(
        second / "Sources/SecondProjectSentinel.swift"
    )

    result = search_calls(
        installed_search, [("first-session", str(first), "SecondProjectSentinel")]
    )[0]

    assert "outside repository" in result
    assert f"repository '{first}'" in result
    assert "candidate_id:" not in result


def test_sources_dir_cannot_select_a_different_repository_without_session_context(
    installed_search,
):
    plugin, first, _, _ = installed_search

    result = search_calls(
        installed_search, [("unknown-session", str(first), "FirstProjectSentinel")]
    )[0]

    assert "outside repository" in result
    assert f"repository '{plugin.resolve()}'" in result
    assert "candidate_id:" not in result
