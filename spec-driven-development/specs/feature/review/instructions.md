# Feature — Validation Rules

Rules applied by `validate-spec` to feature-type specs. Structural checks verify the shape from `feature/rule.md`; buildability checks catch vagueness and implementation leaking.

## Phase A — Structural Checks

* [ ] A.1 **Frontmatter** — `number`, `feature`, `type: feature`, `status`, `blocked-by`, `blocking`, `parent`.

* [ ] A.2 **Required sections (in order):** Title, Description, Input / Output, User Stories, Connects To, Diagrams, Definition of Done.

* [ ] A.3 **Conditional sections** — apply rules from `feature/rule.md`:
  * `## Technical Requirements` required if description/stories mention business logic, integration, APIs, or external systems.

  * `## UI / Mockup` required if description/stories mention screens, views, components, or user interaction. Placeholder-only (`<!-- TODO -->`) counts as missing.

  * `## Test Plan` required when behavior is testable (almost always; skip only for pure internal/infrastructure stories).

  * `## Current State` required only if `mode: rewrite`.

* [ ] A.4 **Diagrams completeness** — `## Diagrams` contains at minimum connection + flow. Sequence diagram required if the spec mentions async operations, callbacks, delegates, notifications, network calls, or multiple distinct actors.

* [ ] A.5 **Forbidden sections** — flag presence of `## Features` list (features don't break into child features — use subtasks).

## Phase B — Buildability Scan (Standard)

* [ ] B.1 **User story quality:**
  * Each story must follow `As a [user/system], I want [goal] so that [reason]` format.

  * Each acceptance criterion must be independently verifiable — flag "works correctly", "handles edge cases", "behaves as expected", or any criterion requiring interpretation.

  * Flag stories with no acceptance criteria.

  * Flag acceptance criteria that describe implementation rather than observable behavior.

* [ ] B.2 **Vague terms** — words that hide decisions:
  * "appropriate", "safe default", "suitable", "proper", "as needed", "handle errors", "relevant", "etc.".

  * For each: what specific value, behavior, or choice is meant?

* [ ] B.3 **Undefined types** — types, protocols, or models referenced but never defined:
  * No fields listed, no signature given, no link to an existing definition.

  * For each: what are the fields/methods/conformances?

* [ ] B.4 **Intent-described operations** — workflow steps that describe what should happen but not how:
  * "instantiate with config", "parse the response", "validate input", "set up the connection".

  * Do NOT flag operations that include pseudo-code, algorithms, or step-by-step logic explaining how it works.

  * For each: what is the concrete initializer, method, or API call?

* [ ] B.5 **Implicit consumer contracts** — outputs produced but no specification of:
  * Who holds the instance and what's its lifetime (owned, shared, transient)?

  * How is it passed to consumers (init injection, environment, closure, return value)?

  * For each: who consumes this, via what mechanism?

* [ ] B.6 **Unverified external APIs** — references to third-party libraries or system frameworks where:
  * Method signatures are described by intent rather than actual API.

  * Version or availability constraints are not mentioned.

  * For each: what is the actual method signature?

* [ ] B.7 **Ambiguous scope boundaries** — places where it's unclear what this spec owns vs what another spec/module owns:
  * Shared types referenced but not assigned to a module.

  * Behaviors that could live in this feature or an adjacent one.

  * For each: who owns this?

* [ ] B.8 **Implementation leaking** — no language-specific syntax in specs. All requirements must be behavioral.
  * **Flag**: backtick-wrapped code, type names, method signatures, attributes, decorators, framework-specific types, protocol conformances, generic constraints.

  * **Allowed**: pseudo-code, algorithms, math, diagrams, design pattern names (strategy, factory, decorator), schema contracts, naming a framework or API as the chosen approach without mandating its syntax.

  * Skip findings already flagged by B.1 (acceptance criteria describing implementation).

  * For each: rewrite as the behavioral requirement it's trying to express.

* [ ] B.9 **AC-architecture disconnects** — acceptance criteria that describe behavior without a traceable path through the spec's architectural model:
  * For each AC describing a state change or user interaction outcome: does the spec's Technical Requirements or architecture description define a mechanism (method, operation, data flow) that performs it?

  * For each architectural mechanism described in Technical Requirements (e.g., "single method", "unified API", "one callback"): does it handle ALL the interaction types visible in the mockups and described in ACs?

  * Flag when an AC says "X updates Y" but no described operation covers that update for all contexts shown in mockups.

  * Flag when Technical Requirements claim a unified mechanism but ACs or mockups show interactions with different semantics that the mechanism doesn't distinguish.

  * For each: which AC is ungrounded, and what architectural mechanism is missing or underspecified?

## Phase C — Scope & Cohesion

Applies the metrics from [README § Scope Metrics](../../README.md#scope-metrics). The validate-spec orchestrator runs four subagents under this phase: three measurement subagents in parallel, then one synthesis pass.

* [ ] C.0 **Applicability gate** — skip Phase C entirely if the spec has `## Subtasks` AND no `## Technical Requirements` AND no own acceptance criteria. The feature is acting as an index for subtasks; size and cohesion live in the children. If skipped, emit no Phase C findings and proceed to Reporting.

* [ ] C.1 **Measurement (parallel)** — three subagents, launched in a single message:
  * `predict-loc-heuristic-agent` (Haiku) — counts ACs + screens, applies `(AC × 12) + (screens × 80)`, emits `heuristic.json`.

  * `predict-loc-skeleton-agent` (Sonnet) — sketches declaration-only code in the project's language (default Swift), counts skeleton LOC, applies a per-language multiplier, emits `skeleton.json`.

  * `cohesion-cluster-agent` (Sonnet) — extracts 4 signals per AC (data type, screen, integration, lifecycle phase), runs 2-signal transitive clustering, labels each group, emits `cohesion.json`.

* [ ] C.2 **Synthesis (sequential)** — `scope-synthesize-agent` (Haiku) reads all three measurement JSONs, computes `consensus_loc = max(heuristic, skeleton × multiplier)`, derives the verdict per the truth table below, generates split candidates from cohesion groups, and emits `scope-assessment.json` (the public contract).

* [ ] C.3 **Findings emission** — translate `scope-assessment.json` into Phase C findings:

  | scope-assessment                                  | Finding category        | Severity                                           |
  | ------------------------------------------------- | ----------------------- | -------------------------------------------------- |
  | `size.severity == MINOR` or `SEVERE`              | `scope_oversized`       | from `size.severity`                               |
  | `cohesion.severity == MINOR` or `SEVERE`          | `incohesive`            | from `cohesion.severity`                           |
  | `verdict == needs_split` AND `driver == size`     | `oversized_cohesive`    | SEVERE                                             |
  | `verdict == needs_split` AND `driver == cohesion` | `split_recommendation`  | SEVERE — body lists `candidate_subtasks`           |
  | `size.calibration_drift == true`                  | `loc_calibration_drift` | MINOR — flags formula vs skeleton divergence > 50% |

## Reporting

* Group findings by category: `structural`, `user_story_quality`, `vague_term`, `undefined_type`, `intent_described`, `implicit_contract`, `unverified_api`, `ambiguous_scope`, `implementation_leaking`, `ac_architecture_disconnect`, `scope_oversized`, `incohesive`, `oversized_cohesive`, `split_recommendation`, `loc_calibration_drift`.

* Per finding: `category`, `location` (section or phrase), `question` (what needs to be answered), and for Phase C: `severity` (MINOR / SEVERE) plus the per-input counts that produced the metric.

* Verdict:

  * `pass` — 0 findings across all phases.

  * `needs_clarification` — any Phase A or B finding, or any Phase C finding at SEVERE.

  * `advisory` — only Phase C findings at MINOR (spec is buildable but worth reviewing).

