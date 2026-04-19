---
paths:
  - "**/*.py"
  - "**/*.sh"
---

# Scripts & Tests

When **creating or modifying** any `.py` or `.sh` script in the repo:

1. **Write tests** in the matching `tests/` folder before considering the work done. Cover the contract — inputs, outputs, error paths — not internal implementation detail.
2. **Run the tests** and confirm green before ending the turn:
   ```bash
   python3 -m unittest discover -s scripts/tests -v
   python3 -m unittest discover -s skills/<name>/scripts/tests -v
   ```
3. **No test = not done.** A script change without a passing test counts as incomplete.

**Test style**:
- Use `subprocess` to invoke the script via its CLI. That tests the contract other code depends on.
- Always use `sys.executable` so tests run with the same Python as the caller.
- No imports that bypass the CLI contract.

**Python version**: if a script uses syntax requiring a specific version, check `python3 --version` first and rewrite to be compatible if needed.

**Scope-specific notes**:
- `mcp-server/` — mode registry changes (`modes.py`) require updated `test_modes.py` assertions. Gateway/server signature changes must be verified via a direct `gateway.py` subprocess call.
- Hook-facing wrappers (e.g. `scripts/regen-token-docs.py`) — test the JSON output shape and the `hookSpecificOutput` field.
