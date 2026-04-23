#!/usr/bin/env python3
"""Apple build MCP server — tuist / xcodebuild / swift build with autodiscovery.

Autodiscovery priority (walks up from project_path):
  1. Tuist.swift exists        → tuist (via Tuist/scripts/tq if present, else raw tuist)
  2. *.xcworkspace exists      → xcodebuild -workspace
  3. *.xcodeproj exists        → xcodebuild -project
  4. Package.swift exists      → swift build

Tools:
  build_target(target, project_path?, configuration?)  → {status, errors, warnings, duration_s}
  run_tests(target, project_path?, test_targets?, skip_ui_tests?)  → {status, passed, failed, errors, duration_s}
  detect_build_system(project_path?)  → {system, root, command}

Run: python3 mcp-server/build/apple/server.py
"""
import json
import os
import re
import subprocess
import sys
import time
import threading
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

# Reuse the protocol from the parent mcp-server directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from protocol import MCPServer

server = MCPServer("apple-build", "1.0.0")

# ─── Build lock (prevents parallel builds on the same project) ───────────────
_build_locks: dict = {}
_locks_mutex = threading.Lock()

def _get_lock(root: Path) -> threading.Lock:
    with _locks_mutex:
        if root not in _build_locks:
            _build_locks[root] = threading.Lock()
        return _build_locks[root]


# ─── Autodiscovery ────────────────────────────────────────────────────────────

def _find_project_root(start: Path):
    """Walk up from start, return (system, root) where system is one of:
    'tuist', 'xcodebuild-workspace', 'xcodebuild-project', 'swift'.
    Returns ('unknown', start) if nothing found.
    """
    p = start.resolve()
    while p != p.parent:
        if (p / "Tuist.swift").exists():
            return "tuist", p
        workspaces = [f for f in p.glob("*.xcworkspace")
                      if not f.name.endswith(".xcodeproj")]
        if workspaces:
            return "xcodebuild-workspace", p
        projects = list(p.glob("*.xcodeproj"))
        if projects:
            return "xcodebuild-project", p
        if (p / "Package.swift").exists():
            return "swift", p
        p = p.parent
    return "unknown", start


def _resolve_root(project_path) -> Path:
    if project_path:
        return Path(project_path).resolve()
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(cwd).resolve()


# ─── Output filtering (mirrors tq-filter.awk) ────────────────────────────────
_SIGNAL_PATTERNS = [
    re.compile(r"^\[x\]"),                       # tuist compile error
    re.compile(r"^\[!\]"),                       # tuist/swiftlint warning
    re.compile(r"warning:"),
    re.compile(r"error:"),
    re.compile(r"BUILD FAILED"),
    re.compile(r"recorded an issue"),
    re.compile(r"^\s*✖ "),
    re.compile(r"failed after .* issue"),
    re.compile(r"unable to resolve"),
]

def _filter_output(output: str) -> str:
    """Keep only signal lines — same rules as tq-filter.awk."""
    kept = [l for l in output.splitlines()
            if any(p.search(l) for p in _SIGNAL_PATTERNS)]
    return "\n".join(kept)


# ─── Log helpers ─────────────────────────────────────────────────────────────

def _log_dir(root: Path) -> Path:
    return root / ".tq-logs"

def _tq_logs_script(root: Path):
    """Return path to tq-logs if it exists, else None."""
    p = root / "Tuist" / "scripts" / "tq-logs"
    return p if p.is_file() else None

def _write_log(root: Path, kind: str, content: str) -> None:
    d = _log_dir(root)
    d.mkdir(exist_ok=True)
    (d / f"{kind}.log").write_text(content, encoding="utf-8")

def _run_tq_logs(root: Path, *args) -> str:
    tql = _tq_logs_script(root)
    if not tql:
        return ""
    r = subprocess.run([str(tql)] + list(args), cwd=str(root),
                       capture_output=True, text=True)
    return r.stdout or r.stderr


def _xcresulttool(xcresult: Path, *args) -> dict:
    """Run xcrun xcresulttool and return parsed JSON."""
    cmd = ["xcrun", "xcresulttool", "get", "--path", str(xcresult),
           "--format", "json"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def _xcresult_failures(xcresult: Path) -> str:
    """Extract failing test summaries from an xcresult bundle."""
    data = _xcresulttool(xcresult)
    lines = []
    for action in data.get("actions", {}).get("_values", []):
        result = action.get("actionResult", {})
        summary_ref = result.get("testsRef", {})
        if not summary_ref:
            continue
        summary_id = summary_ref.get("id", {}).get("_value", "")
        summary = _xcresulttool(xcresult, "--id", summary_id)
        for tgroup in summary.get("summaries", {}).get("_values", []):
            for tsuite in tgroup.get("testableSummaries", {}).get("_values", []):
                for test in tsuite.get("tests", {}).get("_values", []):
                    _collect_failures(test, lines)
    return "\n".join(lines) if lines else "(no failures found)"


def _collect_failures(node: dict, out: list, depth: int = 0) -> None:
    name = node.get("name", {}).get("_value", "")
    status = node.get("testStatus", {}).get("_value", "")
    if status == "Failure":
        out.append(f"FAIL  {name}")
        for msg in node.get("failureSummaries", {}).get("_values", []):
            text = msg.get("message", {}).get("_value", "")
            loc = msg.get("sourceCodeContext", {}).get("location", {})
            line = loc.get("lineNumber", {}).get("_value", "")
            out.append(f"      {text}" + (f" (line {line})" if line else ""))
    for child in node.get("subtests", {}).get("_values", []):
        _collect_failures(child, out, depth + 1)


# ─── Build runners ────────────────────────────────────────────────────────────

def _run(cmd, cwd: Path, timeout: int = 300):
    result = subprocess.run(
        cmd, cwd=str(cwd),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=timeout,
    )
    return result.returncode, result.stdout


def _build_result(rc: int, out: str, tq_handled_log: bool, root: Path,
                  kind: str = "build") -> str:
    """Write log and return filtered signal text for the agent."""
    if not tq_handled_log:
        _write_log(root, kind, out)
    # For tq: stdout is already filtered; for others: filter now
    return out.strip() if tq_handled_log else (_filter_output(out) or
           ("✓ Build succeeded" if rc == 0 else "** BUILD FAILED **"))


def _build_tuist(root: Path, target: str, configuration: str) -> str:
    tq = root / "Tuist" / "scripts" / "tq"
    if tq.is_file():
        cmd = [str(tq), "build", target]
    else:
        cmd = ["tuist", "build", target, "--configuration", configuration]
    with _get_lock(root):
        rc, out = _run(cmd, root)
    return _build_result(rc, out, tq_handled_log=tq.is_file(), root=root)


def _build_xcodebuild(root: Path, target: str, configuration: str,
                       system: str) -> str:
    if system == "xcodebuild-workspace":
        ws = next(f for f in root.glob("*.xcworkspace")
                  if not f.name.endswith(".xcodeproj"))
        cmd = ["xcodebuild", "-workspace", str(ws),
               "-scheme", target, "-configuration", configuration, "build"]
    else:
        proj = next(root.glob("*.xcodeproj"))
        cmd = ["xcodebuild", "-project", str(proj),
               "-scheme", target, "-configuration", configuration, "build"]
    with _get_lock(root):
        rc, out = _run(cmd, root)
    return _build_result(rc, out, tq_handled_log=False, root=root)


def _build_swift(root: Path, target: str, configuration: str) -> str:
    cfg = "debug" if configuration.lower() == "debug" else "release"
    cmd = ["swift", "build", "--target", target, "-c", cfg]
    with _get_lock(root):
        rc, out = _run(cmd, root)
    return _build_result(rc, out, tq_handled_log=False, root=root)


def _test_xcodebuild(root: Path, target: str, system: str) -> str:
    xcresult = _log_dir(root) / "test.xcresult"
    xcresult_path = str(xcresult)
    if system == "xcodebuild-workspace":
        ws = next(f for f in root.glob("*.xcworkspace")
                  if not f.name.endswith(".xcodeproj"))
        cmd = ["xcodebuild", "test", "-workspace", str(ws), "-scheme", target,
               "-resultBundlePath", xcresult_path]
    else:
        proj = next(root.glob("*.xcodeproj"))
        cmd = ["xcodebuild", "test", "-project", str(proj), "-scheme", target,
               "-resultBundlePath", xcresult_path]
    _log_dir(root).mkdir(exist_ok=True)
    with _get_lock(root):
        rc, out = _run(cmd, root, timeout=600)
    return _build_result(rc, out, tq_handled_log=False, root=root, kind="test")


def _test_tuist(root: Path, target: str, test_targets,
                skip_ui: bool) -> str:
    tq = root / "Tuist" / "scripts" / "tq"
    if tq.is_file():
        cmd = [str(tq), "test", target]
        if test_targets:
            cmd += ["--test-targets", ",".join(test_targets)]
        if skip_ui:
            cmd += ["--skip-ui-tests"]
    else:
        cmd = ["tuist", "test", target]
        if test_targets:
            cmd += ["--test-targets", ",".join(test_targets)]
    log_kind = "ui-test" if skip_ui else "test"
    with _get_lock(root):
        rc, out = _run(cmd, root, timeout=600)
    return _build_result(rc, out, tq_handled_log=tq.is_file(), root=root, kind=log_kind)


# ─── MCP tools ────────────────────────────────────────────────────────────────

@server.tool(
    name="build_target",
    description=(
        "Build a Swift/Xcode/Tuist target. Auto-detects the build system "
        "(tuist, xcodebuild, swift build) by scanning up from project_path. "
        "Returns structured errors and warnings — no raw terminal parsing needed."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Scheme or target name to build (e.g. 'ClaudeCodeInspector', 'FoundationExtensions')",
            },
            "project_path": {
                "type": "string",
                "description": "Absolute path to the project root or any file inside it. Defaults to CLAUDE_PROJECT_DIR.",
            },
            "configuration": {
                "type": "string",
                "enum": ["Debug", "Release"],
                "description": "Build configuration. Default: Debug.",
            },
        },
        "required": ["target"],
    },
)
def build_target(target: str, project_path: str = None,
                 configuration: str = "Debug") -> dict:
    root_path = _resolve_root(project_path)
    system, root = _find_project_root(root_path)

    if system == "tuist":
        return _build_tuist(root, target, configuration)
    elif system in ("xcodebuild-workspace", "xcodebuild-project"):
        return _build_xcodebuild(root, target, configuration, system)
    elif system == "swift":
        return _build_swift(root, target, configuration)
    else:
        return {
            "status": "error",
            "message": f"No recognised build system found scanning up from {root_path}",
            "errors": [], "warnings": [],
        }


@server.tool(
    name="run_tests",
    description=(
        "Run tests for a Swift/Xcode/Tuist target. Auto-detects the build system. "
        "Returns pass/fail counts and structured error details."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Scheme or target name (e.g. 'ClaudeCodeInspector', 'FoundationExtensions')",
            },
            "project_path": {
                "type": "string",
                "description": "Absolute path to the project root or any file inside it. Defaults to CLAUDE_PROJECT_DIR.",
            },
            "test_targets": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of specific test targets to run (tuist only).",
            },
            "skip_ui_tests": {
                "type": "boolean",
                "description": "Skip UI test targets (tuist only). Default: false.",
            },
        },
        "required": ["target"],
    },
)
def run_tests(target: str, project_path: str = None,
              test_targets: list = None, skip_ui_tests: bool = False) -> dict:
    root_path = _resolve_root(project_path)
    system, root = _find_project_root(root_path)

    if system == "tuist":
        return _test_tuist(root, target, test_targets or [], skip_ui_tests)
    elif system in ("xcodebuild-workspace", "xcodebuild-project"):
        return _test_xcodebuild(root, target, system)
    else:
        return {
            "status": "error",
            "message": f"run_tests not supported for system: {system}",
            "errors": [], "passed": 0, "failed": 0,
        }


@server.tool(
    name="detect_build_system",
    description="Detect the build system for a project without running a build.",
    input_schema={
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Absolute path to the project root or any file inside it. Defaults to CLAUDE_PROJECT_DIR.",
            },
        },
    },
)
def detect_build_system(project_path: str = None) -> dict:
    root_path = _resolve_root(project_path)
    system, root = _find_project_root(root_path)
    tq = root / "Tuist" / "scripts" / "tq"
    example = {
        "tuist": f"{tq if tq.is_file() else 'tuist'} build <target>",
        "xcodebuild-workspace": "xcodebuild -workspace <ws> -scheme <target> build",
        "xcodebuild-project": "xcodebuild -project <proj> -scheme <target> build",
        "swift": "swift build --target <target>",
        "unknown": "(no build system found)",
    }.get(system, "")
    return {
        "system": system,
        "root": str(root),
        "has_tq": tq.is_file(),
        "example_command": example,
    }


@server.tool(
    name="get_log",
    description=(
        "Return the raw build or test log written by the last build_target / run_tests call. "
        "Use this when you need to see output beyond the structured errors — e.g. linker details, "
        "SwiftLint warnings, or verbose compiler notes."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["build", "test", "ui-test"],
                "description": "Which log to read. Default: build.",
            },
            "project_path": {"type": "string"},
            "tail": {
                "type": "integer",
                "description": "Return only the last N lines. Omit for full log.",
            },
            "failures_only": {
                "type": "boolean",
                "description": "For test/ui-test logs: show full output for failed tests only, trim passing ones. Default: true for test kinds.",
            },
        },
    },
)
def get_log(kind: str = "build", project_path: str = None,
            tail: int = None, failures_only: bool = None) -> str:
    root_path = _resolve_root(project_path)
    _, root = _find_project_root(root_path)
    tql = _tq_logs_script(root)
    if failures_only is None:
        failures_only = kind in ("test", "ui-test")
    if tql:
        if failures_only and kind in ("test", "ui-test"):
            return _run_tq_logs(root, "failures", kind)
        args = ["tail", kind] + (["-n", str(tail)] if tail else [])
        return _run_tq_logs(root, *args)
    log = _log_dir(root) / f"{kind}.log"
    if not log.exists():
        return f"No {kind}.log found. Run build_target/run_tests first."
    lines = log.read_text(encoding="utf-8").splitlines()
    if failures_only and kind in ("test", "ui-test"):
        filtered, block = [], []
        for line in lines:
            if re.search(r"Test Case .+ started", line):
                block = [line]
            elif re.search(r"Test Case .+ failed", line):
                block.append(line); filtered.extend(block); block = []
            elif re.search(r"Test Case .+ passed", line):
                block = []
            else:
                block.append(line)
        lines = filtered or lines
    return "\n".join(lines[-tail:] if tail else lines)


@server.tool(
    name="get_test_failures",
    description=(
        "List failing test cases with their failure messages from the last run_tests call. "
        "Includes assertion messages that tuist strips from stdout (reads from xcresult)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["test", "ui-test"], "description": "Default: test."},
            "project_path": {"type": "string"},
        },
    },
)
def get_test_failures(kind: str = "test", project_path: str = None) -> str:
    root_path = _resolve_root(project_path)
    _, root = _find_project_root(root_path)
    tql = _tq_logs_script(root)
    if tql:
        return _run_tq_logs(root, "failures", kind)
    xcresult = _log_dir(root) / f"{kind}.xcresult"
    if xcresult.exists():
        return _xcresult_failures(xcresult)
    return f"No {kind}.xcresult found. Run run_tests first."


@server.tool(
    name="get_test_cases",
    description="List all test cases (pass/fail) from the last run_tests call.",
    input_schema={
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["test", "ui-test"], "description": "Default: test."},
            "project_path": {"type": "string"},
        },
    },
)
def get_test_cases(kind: str = "test", project_path: str = None) -> str:
    root_path = _resolve_root(project_path)
    _, root = _find_project_root(root_path)
    tql = _tq_logs_script(root)
    if not tql:
        return "tq-logs not available. Only supported for tuist projects with Tuist/scripts/tq-logs."
    return _run_tq_logs(root, "cases", kind)


@server.tool(
    name="get_test_case",
    description=(
        "Get full details for a single test case — activities, assertion messages, attachments. "
        "Use after get_test_failures to drill into a specific failure."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring matched against test case names or IDs."},
            "kind": {"type": "string", "enum": ["test", "ui-test"], "description": "Default: test."},
            "project_path": {"type": "string"},
        },
        "required": ["query"],
    },
)
def get_test_case(query: str, kind: str = "test", project_path: str = None) -> str:
    root_path = _resolve_root(project_path)
    _, root = _find_project_root(root_path)
    tql = _tq_logs_script(root)
    if not tql:
        return "tq-logs not available. Only supported for tuist projects with Tuist/scripts/tq-logs."
    return _run_tq_logs(root, "case", query, kind)


if __name__ == "__main__":
    import datetime
    _dbg = Path("/tmp/apple-build-mcp.log")
    with open(_dbg, "a") as f:
        f.write(f"\n=== {datetime.datetime.now().isoformat()} ===\n")
        f.write(f"pid={os.getpid()} args={sys.argv}\n")
        f.write(f"stdin.isatty={sys.stdin.isatty()}\n")
        f.write(f"CLAUDE_PLUGIN_ROOT={os.environ.get('CLAUDE_PLUGIN_ROOT','(not set)')}\n")
    server.run()
