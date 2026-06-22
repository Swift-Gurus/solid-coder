# Gate Output Path Isolation — Handoff

## What problem are we fixing

The `pre_write_gate` health-check blocks writes to **unrelated files** (e.g. `BaseConfiguration.swift`)
because violations from a previous gate check of an **unrelated file**
(`ElephantFileViewerViewController.swift`) persist in a shared output directory and are re-read
on every subsequent gate invocation within the same Claude session.

### Evidence

**Gate log** (`~/.solid-coder/-Users-crowea-Developer-Autodesk-build-mobile-ios/gate.log`):
```
22:40 — DENY  ElephantFileViewerViewController.swift: 13 violations
22:52 — DENY  ElephantSheetViewerFactory.swift: 6 violations     ← 6 = same as Elephant
23:05 — DENY  Target+Module.swift: 6 violations                  ← still Elephant's
23:17 — DENY  BaseConfiguration.swift: 7 violations              ← still Elephant's
```

`Target+Module.swift` and `BaseConfiguration.swift` have **no violations of their own**.
The 6 violations reported are all for `ElephantFileViewerViewController.swift`.

**Stale files confirmed at:**
```
~/.solid-coder/-Users-crowea-Developer-Autodesk-build-mobile-ios/gate/
  40278d6a-6056-47da-a53e-3085b5445c11/
    structured-concurrency/review-output.json   ← SC-2 violations for Elephant
    swiftui/review-output.json                  ← SUI-1/3/6 violations for Elephant
```

---

## Root cause

**`hooks/hc_checker.py` line 422:**
```python
output_dir = str(solid_coder_project_dir() / "gate" / parent_session_id)
```

Every gate invocation in the same session uses the **same** `gate/<session_id>/` directory.
The LLM reviewer has `Read` + `search_codebase` tools, so when reviewing
`Target+Module.swift` it can crawl `ElephantFileViewerViewController.swift`, find violations
there, and submit them via `submit_batch_findings`. Those cross-file findings land in the
shared session directory. On the next gate check the `ViolationExtractor` globs
**all** `*/review-output.json` under that directory and reports stale violations as blocking
the current write.

**Contrast with `/review` and `/refactor` workflows:**
`mcp-server/pipeline/server.py` `get_output_path()` already generates a **timestamped, unique**
directory per invocation:
```python
ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
dir_name = f"{operation}-{ts}"     # e.g.  review-20260609223000
# → ~/.solid-coder/<slug>/review-20260609223000/
```
Valid operations: `"review"`, `"refactor"`, `"implement"`, `"validate-spec"`.
`"health"` is **not yet listed** but the code handles it via the `else` branch.

---

## Solution

Use `get_output_path("health")` for each gate invocation so every health-check gets its own
isolated timestamped directory. This matches the `/review` pattern exactly.

### Gateway call pattern (already used in hooks layer)

`hooks/hc_rule_loader.py` shows how to call a pipeline server function from the hooks layer:
```python
self._invoker.invoke("get_output_path", extra_args=["--operation", "health"], result_key="output_root")
```

`get_output_path` is **not yet exposed as a gateway CLI subcommand** — that's the first thing
to add.

---

## Files to change

| File | What |
|---|---|
| `mcp-server/pipeline/server.py` | Add `"health"` to `get_output_path()` docstring |
| `mcp-server/gateway.py` | Expose `get_output_path` as CLI subcommand (same pattern as `get_candidate_tags`) |
| `hooks/hc_checker.py` | Add `OutputPathResolving` protocol; wire `LLMHealthChecker` to use it instead of hardcoded path |
| `hooks/hc_checker_factory.py` | Add `GatewayOutputPathResolver`; inject into `make_health_checker()` |

---

## Detailed changes

### 1 — `mcp-server/pipeline/server.py`

Update docstring of `get_output_path()` to list `"health"` as a valid operation:
```python
    Args:
        operation:   "review" | "refactor" | "implement" | "validate-spec" | "health"
```
No logic change needed — the `else` branch already handles any string.

### 2 — `mcp-server/gateway.py`

Add subcommand handler following the existing `get_candidate_tags` pattern so the hooks layer
can call it:
```python
elif subcommand == "get_output_path":
    operation = args.get("operation", "health")
    result = get_output_path(operation)
    print(json.dumps(result))
```

### 3 — `hooks/hc_checker.py`

Add protocol and update `LLMHealthChecker`:
```python
class OutputPathResolving(Protocol):
    def resolve(self, session_id: str) -> str: ...

class LLMHealthChecker:
    def __init__(self, loader, builder, reviewer, path_resolver: OutputPathResolving) -> None:
        ...
        self._path_resolver = path_resolver

    def check(self, content, path, language, parent_session_id) -> Optional[list]:
        principles = self._loader.load(content, path)
        if principles is None:
            return None
        if not principles:
            return []
        output_dir = self._path_resolver.resolve(parent_session_id)   # ← was hardcoded
        prompt = self._builder.build(principles, content, path, parent_session_id, output_dir)
        return self._reviewer.review(prompt, path, output_dir=output_dir)
```

### 4 — `hooks/hc_checker_factory.py`

Add resolver and wire it in:
```python
class GatewayOutputPathResolver:
    def __init__(self, invoker: GatewayInvoking) -> None:
        self._invoker = invoker

    def resolve(self, session_id: str) -> str:
        result = self._invoker.invoke(
            "get_output_path",
            extra_args=["--operation", "health"],
            result_key="output_root",
        )
        if not result:                                    # fallback if gateway unavailable
            from hook_utils import solid_coder_project_dir
            return str(solid_coder_project_dir() / "gate" / session_id)
        return result


def make_health_checker(mcp_config, session_id="", file_path="", log_path=None):
    resolver = GatewayOutputPathResolver(
        invoker=GatewayInvoker(GATEWAY, GatewayCommandRunner())
    )
    return LLMHealthChecker(
        loader=PrinciplesLoader(...),
        builder=HealthPromptBuilder(),
        reviewer=LLMReviewer(...),
        path_resolver=resolver,       # ← new
    )
```

---

## Tests required

Run existing suite first:
```bash
cd /Users/crowea/Developer/Swift-Gurus/solid-coder
python3 -m pytest hooks/tests/ -q
```

### New tests in `hooks/tests/test_hc_checker_batch.py`

**`test_health_checker_uses_resolver_not_hardcoded_path`**
- Inject `FakeOutputPathResolver` returning a known temp path
- Assert the prompt passed to the LLM contains that path (not `gate/<session_id>`)
- Assert cleanup targets that exact path

**`test_each_gate_invocation_gets_unique_output_dir`**
- Call `check()` twice on the same `LLMHealthChecker`
- Resolver returns two different paths
- Assert the two invocations never share output dirs

### New test in `hooks/tests/test_hc_checker_factory.py`

**`test_make_health_checker_injects_gateway_resolver`**
- Build checker via `make_health_checker()`
- Assert `._path_resolver` is a `GatewayOutputPathResolver`

### New test for gateway subcommand

**`test_get_output_path_health_operation`** (in `mcp-server/tests/` or `hooks/tests/`)
- Call gateway with `--operation health`
- Assert returned `output_root` contains `health-` prefix and a valid timestamp
- Assert `"health"` is in the docstring of `get_output_path`

---

## Repo location

```
/Users/crowea/Developer/Swift-Gurus/solid-coder
```

## Quick orientation

```
hooks/
  hc_checker.py           ← LLMHealthChecker, output_dir construction (line 422)
  hc_checker_factory.py   ← make_health_checker(), GatewayInvoker wiring
  hc_rule_loader.py       ← example of existing gateway invoke pattern
  tests/
    test_hc_checker_batch.py   ← tests for output dir, violations, cleanup
    test_pre_write_gate.py     ← gate allow/deny behaviour tests
mcp-server/
  pipeline/server.py      ← get_output_path() definition (line 74)
  gateway.py              ← CLI subcommand dispatcher
```
