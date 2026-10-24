# Plugin runtime release verification — 2026-10-23

Release branch: `codex/fix/NA/plugin-runtime-release-check`; patch version 1.7.20.

## Runtime and distribution

The temporary `run-plugin.py` launcher was removed. Plugin manifests retain their
direct Python commands. Desktop resolves Python to
`/Users/dev/.local/share/mise/installs/python/3.12/bin/python3.12`, backed by
Python 3.12.15. Runtime dependencies were explicitly installed into that interpreter
with user authorization; Pydantic 2.14.1 imports successfully and `pip check` passes.
The installed plugin source cache was not edited.

`requirements-runtime.txt` pins runtime packages. Provision the host interpreter
with `DESKTOP_PYTHON=<absolute Desktop Python> mise run install:desktop`.
The plugin and smoke check do not install dependencies automatically and do not
require the repository's development virtualenv.

## Release checks

- The version-bumper CLI runs smoke before updating either manifest.
- `mise run release:check` requires lint and non-live tests before smoke.
- The GitHub workflow provisions host Python and runs smoke on pull requests,
  main pushes and version tags. Required branch protection must be configured
  separately; remote CI has not been verified by these local checks.

Smoke copies the distribution without its development virtualenv, starts from an
unrelated project and uses an empty temporary home. All eight MCP registrations
and ten hook startups passed using Desktop's base Python. Valid TOML containing
schema-invalid settings produced a gate denial. All four MCP servers in the
already-installed 1.7.19 cache also initialized and listed tools successfully.

Negative regression coverage confirms that an unprovisioned host fails with
missing Pydantic despite a development `PYTHONPATH`, failed smoke leaves versions
unchanged, and nonzero exits or RPC errors cannot count as smoke success.

## Recorded verification

| Group | Tests passed | Subtests passed | Notes |
| --- | ---: | ---: | --- |
| Flow-engine | 1,078 | 96 | Normal host access |
| MCP | 1,400 | 142 | Normal host access; four existing skips |
| Harness/other | 171 | 18 | Normal host access |
| Scripts | 257 | 66 | Includes four smoke regressions |
| Apple/skills | 297 | — | Includes version-bumper regressions |
| Total | 3,203 | 322 | All non-live groups passed |

The complete `mise run release:check` passed with Desktop's interpreter selected
explicitly and normal host access. This includes Ruff, all five non-live test
groups, and installed-package smoke. Earlier sandbox runs encountered SourceKit
and mise access failures; these did not reproduce in the full host run.
`git diff --check` also passed.

SourceKit is supplied by installed Xcode at
`/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/sourcekit-lsp`.
Sandbox SourceKit failures did not reproduce with normal host access; no SourceKit
installation or machine setup change was needed.

## Hook fixes and remaining limits

Gate construction now occurs inside its existing configuration-error handler.
The permission hook's obsolete `OnStopGate` import was replaced by the existing
handler and notifier.

After dependency provisioning, the enabled write gate intercepted a cosmetic
edit to `scripts/release-smoke.py`, but its reviewer failed with
`LLM did not call submit_batch_findings; no output files`. The write was stopped
without retry, bypass or reviewer repair. Audit directory:
`/Users/dev/.solid-coder/-Users-dev-Developer-Swift-Gurus-solid-coder/health-5b9ffec8-d96b-417a-bd29-dbf34f8ab67f`.
Startup smoke does not establish successful live reviewer completion; no
intentional live-model verification was run.

Malformed TOML still falls back to defaults in the existing loader; strict parsing
remains SPEC-071 work. Host Python still requires explicit dependency provisioning.
Plugin source fixes reach installed clients only after release and update.

Raw logs are local, ignored artifacts under
`.solid-coder/.artifacts/plugin-runtime-release-check/2026-10-23/`, including
`desktop-python-smoke-before.log`, `desktop-python-smoke-final.log`,
`desktop-python-mcp-tests-host.log` and `desktop-python-scripts-tests.log`.
