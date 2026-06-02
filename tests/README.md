# Principle Test Harness

Convention-based test infrastructure for principle integration tests.

## Directory structure

```
tests/
  harness/           Python test harness package
    tests/           Unit tests (run via python3 -m unittest discover)
  models/            Model profile TOML files (one per backend)
  principles/        Principle fixture+expectation trees (mirrors references/principles/)
    SRP/
      fixtures/      fixture-N.<ext> source files to review
      expectations/  fixture-N.json expected finding sets
  run_principle_tests.py   CLI entry point
```

The `tests/` tree mirrors `references/` exactly. A `references/<suffix>` argument resolves to `tests/<suffix>`.

## Fixture and expectation convention

Each fixture file `fixtures/fixture-N.<ext>` pairs by stem with `expectations/fixture-N.json`:

```json
{
  "findings": [
    {
      "unit_name": "UserManager",
      "metric_id": "SRP-2",
      "severity": "SEVERE",
      "metrics": { "cohesion_groups": 2 }
    }
  ]
}
```

- `metrics` is optional and skipped from comparison when absent.
- An empty `findings` list marks the fixture compliant — the test passes only if the flow reports no findings.

## Model profiles

Model profiles live in `tests/models/<name>.toml`. Example (`claude.toml`):

```toml
[llm]
backend = "claude"
model = "claude-opus-4-5"
```

Pass `--model <name>` to select a profile. Omit `--model` to use the project `.claude/solid-coder-local.toml`. Adding a new backend means creating a new `tests/models/<name>.toml` — no code change required.

## Running unit tests

```bash
python3 -m unittest discover -s tests/harness/tests -v
```

Run the hooks test suite (includes `hc_config` seam tests):

```bash
python3 -m unittest discover -s hooks/tests -v
```

## Running principle tests (requires live CC+MCP servers)

```bash
python3 tests/run_principle_tests.py \
  --principle references/principles/SRP \
  --flow health \
  --model claude
```

Flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--principle` | required | `references/` path to the principle |
| `--flow` | both | `apply` or `health` |
| `--fixture` | all | restrict to a single fixture stem |
| `--model` | project toml | model profile name |
| `--mode` | `direct` | `direct` (runs flows) or `e2e` (deferred) |
| `--timeout` | 120 | per-fixture timeout in seconds |

Exit code 0 when all fixtures pass, 1 when any fail.

## Output

Per-run output is written to `.solid-coder/logs/tests/<day-time>/<model>/<category-path>/`. This directory is gitignored.
