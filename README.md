# solid-coder

A Claude Code plugin for **spec-driven implementation**, **principle-based review**, and **structured self-correction**.

`solid-coder` is not a single prompt loop. It is a staged workflow system built around:

- spec creation and validation
- code-aware planning
- reuse / modify / create decisions
- rule-aware coding
- structured principle review
- safe correction routed back through `code`

The most important idea is that **rules are applied before code is written, and again after code is written**.

---

## Development setup

Project tooling is declared in `.config/mise/config.toml`: Python 3.12, Ruff,
and Lefthook. Ruby is inherited from the machine's global mise setup. From the
checkout, run:

```bash
mise install
mise run install
mise run lint
mise run test
```

Mise creates and activates the ignored `.venv/` for this project. The install
task installs the Python dependencies from `requirements.txt` there. The existing
Lefthook and conventional-commits setup is unchanged. The lint task checks
without applying fixes; the test task runs non-live suites in separate processes
to preserve their import layout.
Live model checks run separately, after non-live checks pass, and require the
existing model profiles, authentication, and MCP setup. Swift semantic-analysis
tests also require a working Xcode/SourceKit installation on macOS.

Use a mise-activated shell or `mise exec -- <command>` for development tools.
Desktop's Python is provisioned separately below; passing development tests in
the project virtualenv does not verify its dependencies. Changes do not update
an already running desktop app's environment. Personal overrides belong in the ignored
`.config/mise/config.local.toml`.

### Python requirements

Install **Python 3.12** and make `python3.12` available to the Claude/Codex host.
Provision the exact interpreter Desktop resolves, independently of the target
repository's `.venv`. The plugin keeps its direct `python3.12` entrypoints and
does not install dependencies automatically during MCP or hook startup.

```bash
python3.12 --version
```

From this checkout, set `DESKTOP_PYTHON` to that interpreter's absolute path and
run `mise run install:desktop`. For a Desktop using mise's global Python 3.12:

```bash
DESKTOP_PYTHON="$HOME/.local/share/mise/installs/python/3.12/bin/python3.12" mise run install:desktop
```

The explicit executable prevents mise's activated project virtualenv from
redirecting pip to the wrong environment. Only the locked runtime dependencies
are installed; pytest remains a development dependency. From outside the
checkout, the equivalent command is:

```bash
"$DESKTOP_PYTHON" -I -m pip install -r /path/to/solid-coder/requirements-runtime.txt
```

Repeat provisioning when changing the host's Python or updating the runtime
lock. Package-index access or an offline wheelhouse is needed only during this
explicit installation, not during MCP startup. Legacy gateway calls and generated
delegated MCP configurations inherit the running interpreter via `sys.executable`.

After updating the plugin configuration, restart the Claude/Codex session so its
MCP servers are relaunched with the provisioned interpreter. No Python-version
fallback or `SOLID_CODER_PYTHON` override is used. Entry commands are unchanged.

Tree-sitter and its Swift and TypeScript grammars are pinned together in
`requirements-runtime.txt`. Development `requirements.txt` includes that lock
plus pytest. Python 3.9 and the older Swift grammar are no longer part of
the supported dependency configuration.

### Release validation

Run `mise run release:check` before release. This runs Ruff and the non-live
regressions, then `python scripts/release-smoke.py`. The smoke check copies the
distributable plugin to a temporary install, supplies an empty home and base
Python-only PATH, and launches both host manifests from an unrelated directory.
It defaults to the runner's base interpreter, not its active virtualenv; set
`DESKTOP_PYTHON` or pass `--python /absolute/path/to/python3.12` when Desktop uses
a different interpreter. It checks every MCP initialize/tools-list exchange,
every declared hook's startup, and write-gate schema-invalid-config denial.
It never installs or repairs dependencies; an unprovisioned interpreter fails.
It does not use the development `.venv` packages, invoke a model, or establish
that a host dispatched a hook around a real source edit; that remains a separate
live enforcement check.

The version-bumper CLI runs the installed-plugin smoke check before modifying
either manifest; a failure leaves both versions unchanged. The GitHub
`Installed plugin release check` workflow provisions the host Python from the
runtime lock, then runs the same smoke check on pull requests, main pushes, and
`v*` tags. Require its `installed-plugin` status in
branch protection to enforce it for remote merges. The check never publishes a
release or changes the installed plugin cache.

## Core workflows

### `build-spec`
Interactive spec authoring for new or evolving work.

### `build-spec-from-code`
Generate a rewrite-oriented spec from existing code.

### `implement`
Run the staged spec-to-code pipeline:
1. `plan`
2. `validate-plan`
3. `synthesize-implementation`
4. `code`
5. `refactor`

### `refactor`
Run principle-based review and structured correction for changed code.

---

## Workflow overview

```mermaid
flowchart TD
    A[build-spec] --> VS[validate-spec]
    B[build-spec-from-code] --> VS
    VS --> I[implement]
    I --> P[plan]
    P --> VP[validate-plan]
    VP --> SI[synthesize-implementation]
    SI --> C[code]
    C --> R[refactor]
```

---

## Implement flow

```mermaid
flowchart TD
    S[validated spec] --> P[plan]
    P --> VP[validate-plan]
    VP --> SI[synthesize-implementation]
    SI --> D{per component}
    D -->|reuse| RU[reuse existing code]
    D -->|modify| MO[modify existing code]
    D -->|create| CR[create new code]
    RU --> C[code]
    MO --> C
    CR --> C
    C --> R[refactor]
```

---

## Refactor flow

```mermaid
flowchart TD
    A[changed files] --> PRI[prepare-review-input]
    PRI --> DP[discover-principles]
    DP --> APR[apply-principle-review]
    APR --> VF[validate-findings]
    VF --> SF[synthesize-fixes]
    SF --> C[code]
```

---

## Rule discovery and application

The rule system has three layers:

1. **Principle discovery**
2. **Rule / instruction front matter parsing**
3. **Contextual loading inside `code` and `refactor`**

### High-level rule pipeline

```mermaid
flowchart TD
    RP[references/*/rule.md] --> D[discover-principles]
    D --> CT[all_candidate_tags]
    CT --> PRI[prepare-review-input]
    PRI --> MT[matched_tags]
    MT --> D2[discover-principles filtered]
    D2 --> AP[active principles]

    AP --> PF[parse-frontmatter]
    PF --> FL[files_to_load]

    AP --> CODE[code]
    AP --> APR[apply-principle-review]

    FL --> LR[load-reference]
    LR --> CODE
    LR --> APR
```

### What `discover-principles` does

`discover-principles` scans `references/*/rule.md`, parses each rule front matter, and returns:

- `active_principles`
- `skipped_principles`
- `all_candidate_tags`

Rule tags come from each `rule.md` front matter.

Important behavior:

- **untagged rules** are always active
- if no filtering input is provided, all rules are returned as active
- if `matched_tags` are provided, only tagged rules with intersecting tags remain active

This means:
- core rules can always apply
- framework or stack-specific rules activate only when code evidence matches them

---

## How tags are matched

`prepare-review-input` receives `candidate_tags` from the orchestrator and matches them against the code being reviewed.

It uses:
- `detected_imports`
- direct code-pattern inspection
- semantic matching for tags that are not simple import names

Examples:
- `swiftui` can match `import SwiftUI`
- `gcd` can match `DispatchQueue`
- `structured-concurrency` can match `async`, `await`, or `Task {`
- `combine` can match `Publisher` or `Subscriber`

The result is written into `review-input.json` as `matched_tags`.

That file is then fed back into `discover-principles` to narrow the principle set.

---

## Rule front matter vs code front matter

These are different and serve different purposes.

### Rule front matter
Every principle folder has a `rule.md` with front matter such as:

- `name`
- `displayName`
- `category`
- `description`
- `tags`
- `examples`

This front matter is used to:
- identify the principle
- expose candidate tags
- locate examples and referenced files to load

### Code front matter
Generated top-level types can receive semantic comments such as:

- `solid-name`
- `solid-category`
- `solid-stack`
- `solid-description`

This front matter is used to:
- describe the type's role
- improve later discovery in `validate-plan`
- help expose stack or framework context in the codebase

Example:

```swift
/**
 solid-name: DSTheme
 solid-category: design-system theme facade
 solid-stack: swiftui
 solid-description: resolves design tokens for color, spacing, typography, elevation, and motion.
 */
```

`solid-stack` matters because it can help make framework usage more explicit in the codebase, but it is **not** the only signal used for rule activation. Imports and actual code patterns are also part of the discovery story.

---

## How `code` applies rules

`code` does not write first and review later. It loads rules before writing.

### `code` rule-loading flow

```mermaid
flowchart TD
    C0[code phase 1 load context] --> C1[discover-principles]
    C1 --> C2{greenfield?}
    C2 -->|yes| C3[use all principles]
    C2 -->|no| C4[scan source for matched tags]
    C4 --> C5[discover-principles filtered]
    C3 --> C6[parse rule front matter]
    C5 --> C6
    C6 --> C7[load rule.md]
    C6 --> C8[load files_to_load]
    C6 --> C9[load fix/instructions.md]
    C7 --> CW[write code with constraints]
    C8 --> CW
    C9 --> CW
    CW --> SC[self-check against rules and acceptance criteria]
```

### What actually gets loaded in `code`

For each active principle:

1. `discover-principles` returns the active principle folder
2. `parse-frontmatter` reads the principle's `rule.md`
3. `files_to_load` is built from front matter fields like:
   - `examples`
   - `required_patterns`
   - `rules`
4. `load-reference` loads:
   - the `rule.md`
   - referenced examples and patterns
   - `fix/instructions.md`

Those files stay in context while code is being written.

That means `code` writes with:
- the metrics from `rule.md`
- the examples from each principle
- the repair strategies from `fix/instructions.md`

Then `code` performs a self-check against:
- all loaded rules
- per-plan acceptance criteria
- top-level cross-cutting acceptance criteria

---

## How `refactor` applies rules

`refactor` uses the same principle system, but in a different order and for a different purpose.

It is a review-and-correction orchestrator.

### Refactor execution shape

1. discover all principles and collect candidate tags
2. prepare normalized `review-input.json`
3. match tags from real code
4. rediscover principles using those matched tags
5. run one review per active principle
6. validate findings
7. synthesize cross-principle fix plans
8. send those plans back through `code`

This makes `refactor` a structured correction pipeline, not a loose review prompt.

---

## How `apply-principle-review` works

`apply-principle-review` is the generic review runner.

It is not hardcoded to SRP, OCP, SwiftUI, or any single principle. It works from a principle folder.

### Input
It receives:
- principle name / folder
- output path
- `review-input.json`

### Execution steps

```mermaid
flowchart TD
    RI[review-input.json] --> APR[apply-principle-review]
    PF1[parse review/instructions.md front matter] --> APR
    PF2[parse rule.md front matter] --> APR
    APR --> LR1[load referenced review rules]
    APR --> LR2[load rule examples and patterns]
    APR --> U[iterate changed units only]
    U --> O[write review-output.json matching output schema]
```

### What it parses
For each principle:

1. parse `review/instructions.md` front matter
   - can point to:
     - rules
     - output schema
2. parse `rule.md` front matter
   - exposes examples / related files
3. load references from both

### What it reviews
It reads `review-input.json`, then:

- iterates file by file
- iterates unit by unit
- only reviews units where `has_changes == true`
- scopes analysis to the unit's line range

That is important: it is not supposed to review the entire file indiscriminately.

### Output
It writes one structured `review-output.json` per principle.

That output is later consumed by:
- `validate-findings`
- `synthesize-fixes`

---

## Why rules fork through both `code` and `refactor`

This is the main execution model:

- `code` uses rules **proactively**
- `refactor` uses the same principles **reactively**

So the same principle ecosystem supports:
- prevention during implementation
- detection during review
- correction during refactor

That is one of the main design strengths of the system.

---

## Front matter parsing details

The repo has a dedicated `parse-frontmatter` skill and script.

Its job is not only to extract YAML. It also:

- resolves local relative paths
- resolves references-root paths for design patterns
- expands `Examples/` automatically when present
- builds a flat `files_to_load` list for consumers

This means front matter is not only documentation. It is also the rule system's file-loading contract.

---

## Expected spec format

Specs are markdown files with YAML front matter.

Typical front matter includes:

- `number`
- `feature`
- `type`
- `status`
- `blocked-by`
- `blocking`
- `parent`

Example:

```md
---
number: SPEC-012
feature: inspector-panel
type: feature
status: ready
blocked-by: []
blocking: []
parent: SPEC-010
---
```

Common sections:

- Description
- Diagrams
- Definition of Done

Feature / subtask specs usually include:
- Input / Output
- User Stories
- Connects To
- Technical Requirements
- UI / Mockup when relevant

---

## Documentation

- [Workflow YAML reference](.claude/docs/workflow-yaml-reference.md)
- [Architecture overview](docs/architecture-overview.md)
- [Spec format](docs/spec-format.md)
- [Build spec](docs/build-spec.md)
- [Build spec from code](docs/build-spec-from-code.md)
- [Implement flow](docs/implement-flow.md)
- [Refactor flow](docs/refactor-flow.md)
- [Rules and principles](docs/rules-and-principles.md)
- [Front matter](docs/front-matter.md)
- [Validate spec](docs/validate-spec.md)
- [Orchestrator ideas](docs/orchestrator-ideas.md)
