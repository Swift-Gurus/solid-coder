#!/usr/bin/env python3
"""Apple build MCP server — self-contained, no client-side dependencies.

Build system autodiscovery (walks up from project_path):
  Tuist.swift     → tuist install + tuist generate --no-open + tuist build/test
  *.xcworkspace   → xcodebuild -workspace
  *.xcodeproj     → xcodebuild -project
  Package.swift   → swift build / swift test

All raw output is written to {project}/.solid_coder/logs/.
Console output (tool response) is filtered to signal lines only:
  file:line:col: severity: message  (one line per issue)
  ✓ succeeded  |  ** FAILED **
"""
import json
import os
import re
import subprocess
import sys
import threading
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from protocol import MCPServer

server = MCPServer("apple-build", "1.0.0")

# ─── Locks ────────────────────────────────────────────────────────────────────
_locks: dict = {}
_lock_mutex = threading.Lock()

def _lock(root: Path) -> threading.Lock:
    with _lock_mutex:
        if root not in _locks:
            _locks[root] = threading.Lock()
        return _locks[root]


# ─── Autodiscovery ────────────────────────────────────────────────────────────

def _detect(start: Path):
    """Walk up from start → (system, root). system: tuist|xcode-ws|xcode-proj|swift|unknown.

    Tuist.swift takes priority even if found higher up — a sub-package xcodeproj inside
    a Tuist project should still be built/tested via tuist from the project root.
    """
    p = start.resolve()

    # First pass: scan the full path for Tuist.swift (highest priority)
    q = p
    while q != q.parent:
        if (q / "Tuist.swift").exists():
            return "tuist", q
        q = q.parent

    # Second pass: find the nearest xcworkspace / xcodeproj / Package.swift
    while p != p.parent:
        ws = [f for f in p.glob("*.xcworkspace") if not f.name.endswith(".xcodeproj")]
        if ws:
            return "xcode-ws", p
        if list(p.glob("*.xcodeproj")):
            return "xcode-proj", p
        if (p / "Package.swift").exists():
            return "swift", p
        p = p.parent

    return "unknown", start

def _root(project_path=None) -> Path:
    if project_path:
        return Path(project_path).resolve()
    return Path(os.getcwd()).resolve()


# ─── Logs ─────────────────────────────────────────────────────────────────────

def _log_dir(root: Path) -> Path:
    d = root / ".solid_coder" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _save(root: Path, name: str, content: str) -> Path:
    p = _log_dir(root) / name
    p.write_text(content, encoding="utf-8")
    return p


# ─── Output filtering ─────────────────────────────────────────────────────────
# Keeps signal lines only — one issue per line in standard format.

_KEEP = [
    re.compile(r"error:"),
    re.compile(r"warning:"),
    re.compile(r"\*\* BUILD FAILED \*\*"),
    re.compile(r"\*\* TEST FAILED \*\*"),
    re.compile(r"✖ "),
    re.compile(r"failed after .* issue"),
    re.compile(r"recorded an issue"),
    re.compile(r"unable to resolve"),
    re.compile(r"^\[x\]"),
    re.compile(r"^\[!\]"),
]

def _filter(output: str) -> str:
    """Keep signal lines + their immediate continuation (the actual reason text)."""
    all_lines = output.splitlines()
    result = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        if any(p.search(line) for p in _KEEP):
            result.append(line)
            # Include the next non-empty line if it doesn't start a new signal
            # (it's the reason/description following the error indicator)
            j = i + 1
            while j < len(all_lines):
                next_line = all_lines[j]
                if not next_line.strip():
                    break
                if any(p.search(next_line) for p in _KEEP):
                    break  # new signal — don't consume it here
                # Continuation line (indented or plain text reason)
                result.append(next_line)
                j += 1
                # Only take one continuation line to keep output concise
                break
        i += 1
    return "\n".join(result)


def _summary(rc: int, output: str, verb: str = "build") -> str:
    """Always-non-empty status + signal lines."""
    errors = len(re.findall(r"\berror:", output, re.IGNORECASE))
    warnings = len(re.findall(r"\bwarning:", output, re.IGNORECASE))
    if rc == 0:
        status = f"✓ {verb} succeeded"
        if warnings:
            status += f" ({warnings} warning{'s' if warnings != 1 else ''})"
    else:
        status = f"** {verb.upper()} FAILED **"
        counts = ", ".join(filter(None, [
            f"{errors} error{'s' if errors != 1 else ''}" if errors else "",
            f"{warnings} warning{'s' if warnings != 1 else ''}" if warnings else "",
        ]))
        if counts:
            status += f" — {counts}"
    signals = _filter(output)
    return f"{status}\n{signals}" if signals else status


# ─── SwiftLint ────────────────────────────────────────────────────────────────

def _run_lint(root: Path) -> str:
    """Run swiftlint on the project, return filtered violations as text."""
    if not _which("swiftlint"):
        return "(swiftlint not found — install via mise or Homebrew)"

    # Find config file
    config = None
    for name in [".swiftlint.yml", ".swiftlint.yaml"]:
        if (root / name).exists():
            config = root / name
            break

    cmd = ["swiftlint", "lint", "--reporter", "json", "--quiet"]
    if config:
        cmd += ["--config", str(config)]

    r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    raw = r.stdout or "[]"
    _save(root, "lint.log", raw)

    try:
        violations = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError:
        return r.stdout or r.stderr or "(no output)"

    if not violations:
        return "✓ lint passed"

    lines = []
    for v in violations:
        f = v.get("file", "")
        # Make path relative if inside project
        try:
            f = str(Path(f).relative_to(root))
        except Exception:
            pass
        line = v.get("line", "")
        col = v.get("character", "")
        rule = v.get("rule_id", "")
        sev = v.get("severity", "").lower()
        reason = v.get("reason", "")
        lines.append(f"{f}:{line}:{col}: {rule} {sev}: {reason}")

    return "\n".join(lines)


def _which(cmd: str) -> bool:
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


# ─── Runners ──────────────────────────────────────────────────────────────────

def _run(cmd, cwd: Path, timeout: int = 600) -> tuple:
    r = subprocess.run(cmd, cwd=str(cwd),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=timeout)
    return r.returncode, r.stdout


def _run_tuist_build(root: Path, target: str, configuration: str) -> str:
    """Full tuist flow: install → generate → build."""
    log = []

    rc, out = _run(["tuist", "install"], root)
    log.append(f"=== tuist install ===\n{out}")
    _save(root, "build.log", "\n".join(log))
    if rc != 0:
        return _summary(rc, out, "tuist install")

    rc, out = _run(["tuist", "generate", "--no-open"], root)
    log.append(f"=== tuist generate ===\n{out}")
    _save(root, "build.log", "\n".join(log))
    if rc != 0:
        return _summary(rc, out, "tuist generate")

    rc, out = _run(["tuist", "build", target, "--configuration", configuration], root)
    log.append(f"=== tuist build ===\n{out}")
    _save(root, "build.log", "\n".join(log))
    return _summary(rc, out, "build")


def _run_xcode_build(root: Path, target: str, configuration: str, system: str) -> str:
    if system == "xcode-ws":
        ws = next(f for f in root.glob("*.xcworkspace") if not f.name.endswith(".xcodeproj"))
        cmd = ["xcodebuild", "-workspace", str(ws), "-scheme", target,
               "-configuration", configuration, "build"]
    else:
        proj = next(root.glob("*.xcodeproj"))
        cmd = ["xcodebuild", "-project", str(proj), "-scheme", target,
               "-configuration", configuration, "build"]
    rc, out = _run(cmd, root)
    _save(root, "build.log", out)
    return _summary(rc, out, "build")


def _run_swift_build(root: Path, target: str, configuration: str) -> str:
    cfg = "debug" if configuration.lower() == "debug" else "release"
    rc, out = _run(["swift", "build", "--target", target, "-c", cfg], root)
    _save(root, "build.log", out)
    return _summary(rc, out, "build")


def _xcresulttool_test_results(xcresult: Path) -> dict:
    """Call xcresulttool with the new test-results API."""
    cmd = ["xcrun", "xcresulttool", "get", "test-results", "tests",
           "--path", str(xcresult)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout) if r.returncode == 0 else {}
    except Exception:
        return {}


def _iter_cases(nodes: list):
    """Walk testNodes tree, yield each Test Case node."""
    for node in nodes:
        if node.get("nodeType") == "Test Case":
            yield node
        yield from _iter_cases(node.get("children", []))


def _count_from_xcresult(xcresult: Path) -> tuple:
    """Return (passed, failed) by reading the xcresult bundle."""
    data = _xcresulttool_test_results(xcresult)
    passed = failed = 0
    for case in _iter_cases(data.get("testNodes", [])):
        result = case.get("result", "")
        if result == "Passed":
            passed += 1
        elif result == "Failed":
            failed += 1
    return passed, failed


def _count_passed(output: str) -> int:
    """Fallback: count from stdout when xcresult not available."""
    m = re.search(r"(\d+) tests? passed", output)
    if m:
        return int(m.group(1))
    return len(re.findall(r"Test Case .+ passed", output))


def _count_failed(output: str) -> int:
    """Fallback: count from stdout when xcresult not available."""
    m = re.search(r"(\d+) tests? failed", output)
    if m:
        return int(m.group(1))
    return len(re.findall(r"Test Case .+ failed", output))


def _run_tuist_test(root: Path, target: str, test_targets: list,
                    skip_ui: bool, skip_unit: bool, only_testing: list) -> str:
    # Mirror tq log naming: skip-unit-tests → ui-test.log, everything else → test.log
    kind = "ui-test" if skip_unit else "test"
    log = []

    rc, out = _run(["tuist", "generate", "--no-open"], root)
    log.append(f"=== tuist generate ===\n{out}")
    _save(root, "build.log", "\n".join(log))
    if rc != 0:
        return _summary(rc, out, "tuist generate")

    xcresult = _log_dir(root) / f"{kind}.xcresult"
    if xcresult.exists():
        import shutil; shutil.rmtree(str(xcresult))

    cmd = ["tuist", "test", target, "--result-bundle-path", str(xcresult)]
    if test_targets:
        cmd += ["--test-targets", ",".join(test_targets)]
    if skip_ui:
        cmd += ["--skip-ui-tests"]
    if skip_unit:
        cmd += ["--skip-unit-tests"]
    if only_testing:
        cmd += ["--"] + [f"-only-testing:{t}" for t in only_testing]

    rc, out = _run(cmd, root, timeout=900)
    log.append(f"=== tuist test ===\n{out}")
    _save(root, f"{kind}.log", "\n".join(log))  # always written

    # Count from xcresult (accurate for both XCTest and swift-testing)
    if xcresult.exists():
        passed, failed = _count_from_xcresult(xcresult)
    else:
        passed, failed = _count_passed(out), _count_failed(out)

    if rc == 0:
        return f"✓ {passed} tests passed"
    status = f"** TESTS FAILED ** — {failed} failed, {passed} passed"
    signals = _filter(out)
    return f"{status}\n{signals}" if signals else status


def _run_xcode_test(root: Path, target: str, system: str, only_testing: list) -> str:
    xcresult = _log_dir(root) / "test.xcresult"
    if xcresult.exists():
        import shutil; shutil.rmtree(str(xcresult))

    if system == "xcode-ws":
        ws = next(f for f in root.glob("*.xcworkspace") if not f.name.endswith(".xcodeproj"))
        cmd = ["xcodebuild", "test", "-workspace", str(ws), "-scheme", target,
               "-resultBundlePath", str(xcresult)]
    else:
        proj = next(root.glob("*.xcodeproj"))
        cmd = ["xcodebuild", "test", "-project", str(proj), "-scheme", target,
               "-resultBundlePath", str(xcresult)]

    for t in only_testing:
        cmd += ["-only-testing", t]

    rc, out = _run(cmd, root, timeout=900)
    _save(root, "test.log", out)
    passed = _count_passed(out)
    failed = _count_failed(out)
    if rc == 0:
        return f"✓ {passed} tests passed"
    status = f"** TESTS FAILED ** — {failed} failed, {passed} passed"
    signals = _filter(out)
    return f"{status}\n{signals}" if signals else status


# ─── xcresult querying ────────────────────────────────────────────────────────

def _xcresult_activities(xcresult: Path, test_id: str) -> str:
    """Fetch and render activity timeline for one test case (UI tests).
    Mirrors tq-extract-activities.py logic.
    """
    cmd = ["xcrun", "xcresulttool", "get", "test-results", "activities",
           "--path", str(xcresult), "--test-id", test_id]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(r.stdout) if r.returncode == 0 else {}
    except Exception:
        return ""

    def iter_all(activities):
        for a in activities:
            yield a
            yield from iter_all(a.get("childActivities", []))

    runs = data.get("testRuns") or []
    if not runs:
        return ""

    times = [a["startTime"] for run in runs
             for a in iter_all(run.get("activities", []))
             if isinstance(a.get("startTime"), (int, float))]
    origin = min(times) if times else 0.0

    def is_noise(a):
        title = a.get("title", "")
        return title.startswith("kXCT") or (a.get("startTime") is None and title.endswith("()"))

    def render(a, depth):
        if is_noise(a): return []
        marker = "✖" if a.get("isAssociatedWithFailure") else "•"
        start = a.get("startTime")
        stamp = f"T+{start - origin:7.3f}s" if isinstance(start, (int, float)) else " " * 11
        lines = [f"{'  ' * depth}{marker} [{stamp}] {a.get('title', '')}"]
        children = [c for c in a.get("childActivities", []) if not is_noise(c)]
        if not children:
            for att in a.get("attachments", []):
                lines.append(f"{'  ' * (depth+1)}↳ {att.get('name') or '(unnamed)'}")
        for child in children:
            lines.extend(render(child, depth + 1))
        return lines

    out = ["    Activities:"]
    for run in runs:
        for a in run.get("activities", []):
            out.extend(render(a, 2))
    return "\n".join(out)


def _xcresult_failures(xcresult: Path, include_activities: bool = False) -> str:
    """Extract failures. For UI tests (include_activities=True), also shows activity timeline."""
    data = _xcresulttool_test_results(xcresult)
    lines = []
    for case in _iter_cases(data.get("testNodes", [])):
        if case.get("result") != "Failed":
            continue
        lines.append(f"  ✖ {case.get('name', '?')}")
        for child in case.get("children", []):
            if child.get("nodeType") == "Failure Message":
                lines.append(f"      {child.get('name', '')}")
        if include_activities:
            test_id = case.get("nodeIdentifier", "")
            if test_id:
                activities = _xcresult_activities(xcresult, test_id)
                if activities:
                    lines.append(activities)
    return "\n".join(lines) if lines else "(no failures)"


# ─── MCP tools ────────────────────────────────────────────────────────────────

@server.tool(
    name="build",
    description=(
        "Build a Swift/Xcode/Tuist target. Auto-detects the build system. "
        "For Tuist: runs install + generate + build. "
        "Returns errors and warnings only, or ✓ on success. "
        "Full log saved to .solid_coder/logs/build.log."
    ),
    input_schema={
        "type": "object",
        "required": ["target"],
        "properties": {
            "target": {"type": "string", "description": "Scheme or target name to build."},
            "project_path": {"type": "string", "description": "Path inside the project. Defaults to CLAUDE_PROJECT_DIR."},
            "configuration": {"type": "string", "enum": ["Debug", "Release"], "description": "Default: Debug."},
        },
    },
)
def build(target: str, project_path=None, configuration: str = "Debug") -> str:
    root = _root(project_path)
    system, root = _detect(root)
    with _lock(root):
        if system == "tuist":
            return _run_tuist_build(root, target, configuration)
        elif system in ("xcode-ws", "xcode-proj"):
            return _run_xcode_build(root, target, configuration, system)
        elif system == "swift":
            return _run_swift_build(root, target, configuration)
        return f"No build system found scanning up from {root}"


@server.tool(
    name="test",
    description=(
        "Run unit tests or UI tests. Auto-detects the build system. "
        "For Tuist: runs generate + test. "
        "Returns failures only, or ✓ N passed. "
        "Saves xcresult to .solid_coder/logs/. Call get_test_failures for details. "
        "Use only_testing to run a specific suite or individual test: "
        "'Target/Suite' for a full suite, 'Target/Suite/testMethod' for one test."
    ),
    input_schema={
        "type": "object",
        "required": ["target"],
        "properties": {
            "target": {"type": "string", "description": "Scheme or target name."},
            "project_path": {"type": "string"},
            "test_targets": {"type": "array", "items": {"type": "string"}, "description": "Filter to specific test targets (Tuist only)."},
            "only_testing": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Run only these tests. Format: 'Target/Suite' (full suite) or "
                    "'Target/Suite/testMethod' (individual test). "
                    "Example: ['MyUITests/LoginTests/testLoginSuccess']"
                ),
            },
            "skip_ui_tests": {"type": "boolean", "description": "Skip UI tests, run unit tests only → test.log. Default: false."},
            "skip_unit_tests": {"type": "boolean", "description": "Skip unit tests, run UI tests only → ui-test.log. Default: false."},
        },
    },
)
def test(target: str, project_path=None, test_targets=None, only_testing=None,
         skip_ui_tests: bool = False, skip_unit_tests: bool = False) -> str:
    root = _root(project_path)
    system, root = _detect(root)
    only = only_testing or []
    with _lock(root):
        if system == "tuist":
            return _run_tuist_test(root, target, test_targets or [],
                                   skip_ui=skip_ui_tests, skip_unit=skip_unit_tests,
                                   only_testing=only)
        elif system in ("xcode-ws", "xcode-proj"):
            return _run_xcode_test(root, target, system, only_testing=only)
        return f"test not supported for build system: {system}"


@server.tool(
    name="lint",
    description=(
        "Run SwiftLint on the project. Returns violations (file:line:col rule severity: reason) "
        "or ✓ lint passed. Raw output saved to .solid_coder/logs/lint.log."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
        },
    },
)
def lint(project_path=None) -> str:
    root = _root(project_path)
    _, root = _detect(root)
    return _run_lint(root)


@server.tool(
    name="get_log",
    description="Return the raw log from the last build/test/lint run for deep inspection.",
    input_schema={
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["build", "test", "ui-test", "lint"], "description": "Default: build."},
            "project_path": {"type": "string"},
            "tail": {"type": "integer", "description": "Return only the last N lines."},
        },
    },
)
def get_log(kind: str = "build", project_path=None, tail: int = None) -> str:
    root = _root(project_path)
    _, root = _detect(root)
    log = _log_dir(root) / f"{kind}.log"
    if not log.exists():
        return f"No {kind}.log found. Run build/test/lint first."
    lines = log.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-tail:] if tail else lines)


@server.tool(
    name="get_test_failures",
    description=(
        "Get detailed failure messages from the last test run (reads xcresult bundle). "
        "Includes assertion messages not shown in the console summary."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["test", "ui-test"], "description": "Default: test."},
            "project_path": {"type": "string"},
        },
    },
)
def get_test_failures(kind: str = "test", project_path=None) -> str:
    root = _root(project_path)
    _, root = _detect(root)
    xcresult = _log_dir(root) / f"{kind}.xcresult"
    if not xcresult.exists():
        return f"No {kind}.xcresult found. Run test first."
    return _xcresult_failures(xcresult, include_activities=(kind == "ui-test"))


@server.tool(
    name="detect_build_system",
    description="Detect which build system this project uses.",
    input_schema={
        "type": "object",
        "properties": {"project_path": {"type": "string"}},
    },
)
def detect_build_system(project_path=None) -> str:
    root = _root(project_path)
    system, root = _detect(root)
    return f"system: {system}\nroot: {root}"


if __name__ == "__main__":
    server.run()
