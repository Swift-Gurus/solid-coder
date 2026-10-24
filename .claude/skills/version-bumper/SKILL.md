---
name: version-bumper
description: Bump the solid-coder plugin version across all plugin.json manifests
argument-hint: [--part major|minor|patch] [--set X.Y.Z]
allowed-tools: Bash(python3 .claude/skills/version-bumper/scripts/bump-plugin-version.py *)
user-invocable: true
---

# Version Bumper

Run:

    python3 .claude/skills/version-bumper/scripts/bump-plugin-version.py $ARGUMENTS

The script updates every `plugin.json` manifest (`.claude-plugin/`, `.codex-plugin/`) together and
fails loudly if they've drifted to different versions rather than guessing which is correct. It
prints `<old> -> <new>` on success.

Before changing either manifest, the CLI runs the clean installed-plugin release
smoke check. A failure blocks the bump and leaves both versions unchanged. It
uses `DESKTOP_PYTHON` when supplied, otherwise the runner's base Python 3.12,
without the repository's virtualenv packages. Provision that interpreter with
`requirements-runtime.txt` first; the smoke check never installs dependencies.

Report the resulting version change to the user.
