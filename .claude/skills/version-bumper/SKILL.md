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

Report the resulting version change to the user.
