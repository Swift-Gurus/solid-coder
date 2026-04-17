# Epic — Validation Rules

Rules applied by `validate-spec` to epic-type specs. Structural checks verify the shape from `epic/rule.md`; buildability checks catch epic-specific vagueness.

## Phase A — Structural Checks

Verify the spec contains everything `rule.md` requires:

- [ ] A.1 **Frontmatter** — `number`, `feature`, `type: epic`, `status`, `blocked-by`, `blocking`. `parent` required for non-root epics.
- [ ] A.2 **Required sections (in order):** Title, Description, User Stories, Features, Diagrams, Connects To, Definition of Done.
- [ ] A.3 **Diagrams completeness** — `## Diagrams` contains at minimum a connection diagram and a flow diagram.
- [ ] A.4 **Current State (conditional)** — required only if `mode: rewrite` is set.
- [ ] A.5 **Forbidden sections** — flag presence of `## Technical Requirements`, `## Test Plan`, `## UI / Mockup`, or `## Input / Output` (these belong in child specs).

## Phase B — Buildability Scan (epic-specific)

- [ ] B.1 **Vague scope** — the epic's purpose must be concrete enough that a developer can tell whether a given task is in or out of scope.
  - Flag phrases like "improve the system", "better UX", "various improvements", "general refactor".
  - For each: what specifically is being changed and why?

- [ ] B.2 **Undefined subtasks** — features listed in the `## Features` breakdown that are named but not scoped.
  - A subtask is undefined if its name alone doesn't communicate what needs to be built.
  - For each: what does this subtask deliver?

- [ ] B.3 **Missing success criteria** — the Definition of Done must state what "done" means for the epic as a whole, not just that subtasks are complete.
  - Flag if DoD says only "all subtasks merged" or similar — what observable outcome does the epic achieve?

- [ ] B.4 **Ambiguous ownership** — behaviors or components that span multiple subtasks without a clear owner.
  - Shared state, shared protocols, or cross-cutting concerns mentioned in the epic but not assigned to a subtask.
  - For each: which subtask owns this?

- [ ] B.5 **Duplication** — the same concepts, flows, or behaviors explained multiple times across different sections.
  - For each: define ownership — which section is the source of truth?
  - Consolidate into corresponding user stories.

- [ ] B.6 **Framework prescription** — epic prescribes a specific framework, library, or technology that should be a child spec's decision.
  - Epics describe what to achieve, not what tools to use.
  - For each: reframe as a capability requirement (e.g., "reactive state management" instead of "use Combine", "unidirectional architecture" instead of "use TCA").

## Reporting

- Group findings by category: `structural`, `vague_scope`, `undefined_subtask`, `missing_success_criteria`, `ambiguous_ownership`, `duplication`, `framework_prescription`.
- Per finding: `category`, `location` (section or phrase), `question` (what needs to be answered).
- Verdict: `pass` (0 findings) or `needs_clarification` (>0 findings).
