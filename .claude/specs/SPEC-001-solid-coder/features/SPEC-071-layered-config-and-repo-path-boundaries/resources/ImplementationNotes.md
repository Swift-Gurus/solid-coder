# Configuration feature handoff

Status: **draft, not implemented**. The approved decision is to merge repository settings over user defaults, rather than use user defaults only when repository files are absent. The alternate repository location intentionally uses the dotted directory `.config/solid.coder`.

## Existing capabilities to reuse

- `mcp-server/health/config/hc_config_core.py` discovers the effective directory, reads root-to-leaf repository/local settings, and supports the explicit test-model profile override.
- `mcp-server/scoring/config_merger.py` recursively merges tables and replaces non-table values.
- Existing typed settings decoding remains the schema authority. Avoid applying per-file default values before merging: those defaults could erase values supplied by lower-precedence files.
- The current generic TOML helper returns defaults on load failures. This feature's selected-file diagnostics require a strict loading boundary for its new discovery path; do not silently treat a malformed preferred alias as absent.

## Delivery boundaries

Solid-coder owns loading, precedence, target containment, and documentation. No `repo:setup` synchronization implementation was found in this repository. Its external owner can synchronize the canonical `.solid-coder/config.toml`; mise can manage the primary user-wide config. Neither global automation nor machine configuration is changed by writing this spec.

Relative source targets resolve against the selected Git root even when supplied by a home config. Keep plugin resource resolution and existing audit/model storage independent. Test normal repositories, worktree marker files, nested directories/repositories, traversal, symlinks, and glob enumeration through both legacy and workflow consumers.

## Readiness

No implementation tests have been added or run for this future behavior. Existing non-live retirement tests do not demonstrate config layering or containment support. Structural/buildability checks and measurements are recorded in `Validation.json` and `scope-assessment.json`. The strict cohesion check recommends three delivery groups (config merging, target execution, separate-resource preservation); `split-plan.json` records the proposal without creating extra specs or claiming those groups are implemented. Resolve that scope recommendation before changing this draft to ready.
