# Agentic Development: Lessons from the Field

A practical guide on building multi-agent AI pipelines — what works, what breaks, and why. Written from real experience building solid-coder, a multi-agent Swift code review and refactoring system, and working with Claude Code on production iOS projects.

---

## Part 1 — Building Blocks

### 1. What Agentic Development Actually Looks Like

An agentic system is not a single large prompt. It is a pipeline of focused, specialized agents — each with a defined input, a defined output, a specific model, and constrained tools. Each agent does one job.

The mental model:

- **Skill** — a set of instructions describing what to do (phases, steps, constraints). The "what."
- **Agent** — a runtime wrapper that loads a skill, sets a model, and restricts tools. The "how."
- **Pipeline** — an ordered composition of agents where the output of one becomes the input of the next. The "when."

In solid-coder, a `/review` run decomposes like this:

```
discover-principles     → which rules apply to this code?
prepare-review-input    → normalize the target into structured JSON
filter-principles       → which rules are active given the imports/tags?
N × principle-review    → parallel agents, one per principle
validate-findings       → filter to only what actually changed
generate-report         → render results as HTML
```

Every agent is disposable. If a step fails, you replace that agent — you don't redesign the pipeline.

### 2. Pipeline Design

A well-designed pipeline has three properties:

**Sequential where there are real dependencies, parallel everywhere else.** Dependency analysis before filtering (you need the candidate tags first), but all principle reviews can run at the same time. Every agent you serialize unnecessarily is time wasted.

**Data contracts between stages.** Each boundary is a JSON file with a schema. The agent upstream writes it. The agent downstream reads it. Neither cares about the other's internals. This is what makes it possible to swap an agent without cascading changes.

**Isolated output directories per run.** Each run writes to `.solid_coder/review-{timestamp}/`. No run can corrupt another run's output. Debugging is trivial — the artifacts are right there.

What breaks pipelines:
- Agents that read state from the environment instead of their inputs (non-deterministic behavior)
- Schemas that differ between what one agent writes and what the next expects (silent mismatches)
- One agent's output being implicitly relied on by a non-adjacent stage

### 3. Parallel Agents

Parallelism in an agentic system means spawning multiple agents in a single message. Each agent gets its own context window, its own model instance, its own tool calls. They don't share state.

In solid-coder, principle reviews run this way — one `principle-review-fx-agent` per active principle, all launched simultaneously:

```
[ SRP review ] [ OCP review ] [ LSP review ] [ ISP review ]
     ↓               ↓               ↓               ↓
  rules/SRP/      rules/OCP/      rules/LSP/      rules/ISP/
review-output   review-output   review-output   review-output
    .json           .json           .json           .json
```

Each writes to its own path. The orchestrator waits for all of them, then collects results.

**Key constraint:** agents that run in parallel cannot depend on each other's output. If they need to share information, that sharing must happen in a prior sequential stage.

**Failure handling in parallel runs:** when one of N agents fails, the question is whether to fail the whole run or continue with partial results. For reviews, continuing with N-1 principles is usually better than halting — the user gets a partial report rather than nothing. For synthesis, where the whole point is cross-principle reasoning, a failure in one principle's review makes the synthesis output untrustworthy.

### 4. Prompt Engineering

Agent instructions are not prose descriptions. They are **phase-structured checklists** with explicit inputs, explicit outputs, and explicit skip conditions.

What works:

```markdown
## Phase 2: Load Context
- [ ] 2.1 Read review-input.json from {OUTPUT_ROOT}/prepare/
- [ ] 2.2 For each file with has_changes == true: load its content
- [ ] 2.3 If no files have has_changes == true: stop and report "nothing to review"
```

What doesn't work:

```markdown
Review the code for SOLID violations and produce findings.
```

The second form gives the agent complete discretion. It will make sensible-looking decisions that quietly diverge from what you intended. The first form leaves no room for interpretation.

**Constraints belong in constraints sections, not scattered in prose.** A constraint buried in a paragraph will be forgotten. A constraint in a numbered list under `## Constraints` will be applied. The most important constraints get repeated across multiple phases because the agent re-reads the skill instructions as it works through them.

---

## Part 2 — Failure Modes

These are not theoretical. All of the examples below came from real sessions.

### 5. Agents Skipping Steps

An agent will skip a step when:
- The step's preconditions aren't met and the agent judges the step "not applicable"
- The step is expensive and the agent finds a plausible reason to shortcut it
- The step is implied (the agent thinks it already did it as part of something else)

The fix is making every skip condition **explicit**. If a step can be skipped, the skill must say exactly when and say exactly what to do instead. "If no UI test suite exists, skip to step 5.6" is a valid skip condition. "Use your judgment" is not.

In practice: if you notice a step being skipped in a session, add explicit language to the skill before the next run. The agent didn't invent the skip — it found an implicit permission in the instructions.

### 6. Non-Idempotent Behavior

Running the same skill on the same code twice can produce different results. This happens for several reasons:

- **Stale external state.** The agent fixes a file, the user rebuilds, and the same error appears. Not because the fix was wrong — because Xcode's build index hadn't been refreshed. The agent's output was correct; the environment wasn't idempotent.

- **Probabilistic sampling.** LLMs are not deterministic. The same prompt can produce subtly different outputs. Metric counts (verb count, cohesion groups) that differ by one between runs can cross a severity threshold.

- **Context window state.** If a skill reads previously generated files during its run and those files were produced by a prior run with different results, the new run starts from a different state.

From a real session:

> After the regen, `TeamInviteView.swift` had `.caption1` and `.callout` — invalid `AlloyTextStyle` cases. Fixed `.callout`. User reported the same error again on the next build. The file on disk was correct. Xcode was using a stale build index.

The non-idempotent part wasn't the agent — it was the environment the agent was operating in. But from the outside, it looked like the fix didn't take.

**Design implication:** agents that write code and then verify by building are vulnerable to environment state. Capturing a baseline before any changes (what errors existed *before* the agent touched anything) makes the delta visible.

### 7. Skills Not Loaded When the Agent Works for Itself

When an agent is given a complex task, it operates in its own context. The skills available to it are only the ones explicitly declared in its agent definition. If a skill isn't listed, the agent doesn't know it exists.

The failure pattern:

1. Agent has a large prompt describing what to do
2. Partway through, it needs to do something that a skill handles
3. Because the skill isn't loaded, the agent doesn't reach for it
4. Instead it improvises — usually by searching, then writing something from scratch

From a real session building a test suite:

> The code agent needed test helpers. It searched for type declarations via Grep — found nothing (because `UITestConveniences` is a local Swift package, not a loose type file). Concluded the helpers didn't exist. Created its own from scratch.

The skill existed. The package existed. But the agent's discovery mechanism only searched for Swift type declarations, not for local package manifests. It filled the blank with something it knew how to make.

The fix was two-pronged:
1. Add a package discovery step to the plan phase — glob for `Packages/*/` and `Package.swift` before decomposing, report available modules as constraints
2. Make the code skill's dependency resolution aware of packages, not just types: "Before writing any helper, check if a local package provides it"

**The general lesson:** when an agent produces something that already exists, the discovery step that should have found it didn't. Don't patch the output — fix the discovery.

### 8. Context Overload → Loss of Focus → Hallucination

When a single agent is given too many things to track at once, it starts producing outputs that look correct but aren't. The agent is reasoning forward from premises it's made up because it lost track of the actual source of truth.

The clearest example from these sessions:

> A code generation step produced `AlloyTextStyle.caption1` and `AlloyTextStyle.callout`. These are not members of `AlloyTextStyle`. They are members of UIKit's `UIFont.TextStyle`. The regen generated a large SwiftUI view that referenced a design system type it had never seen defined. It filled in names it knew from UIKit because they sounded right.

The agent wasn't lying. It was completing a pattern with the closest analogue it had. This is the fundamental risk: when the context is too large and the unknowns are too many, the agent's output becomes a mix of real knowledge and plausible fabrication — with no visible seam between them.

**Signs you're in this failure mode:**
- Names that are close but not quite right (`.caption` vs `.caption1`)
- Types that reference APIs from the wrong framework
- Code that compiles on first read but fails at runtime with "member not found"
- An agent that says "I'm confident this is correct" about something that is subtly wrong

**The fix is never "give the agent more context."** It's to reduce scope. Smaller tasks, tighter constraints, explicit lists of valid values ("valid `AlloyTextStyle` members are: h1, h2, headlineBold, headline, bodyBold, body, caption").

### 9. Too Many Tasks in One Turn (Scope Creep)

Agents drift. Given a large task, they will notice adjacent things and address them — sometimes correctly, sometimes not. This is scope creep, and it makes sessions hard to reason about.

This shows up in two forms:

**Outward scope creep:** the agent does more than asked. It "also noticed" something, "while it was there" fixed something else, "took the liberty" of refactoring a nearby method. The changes may be correct, but they weren't asked for, they weren't reviewed, and they make the diff harder to read.

**Inward scope creep:** the agent splits what should be one coherent change into multiple partial attempts, losing track of the full picture. This is the failure mode that leads to iteration 3 undoing what iteration 1 fixed.

The design countermeasure from solid-coder's architecture:

> Each re-review is stateless. The iteration loop doesn't carry forward any state from the previous iteration — it runs a fresh review on modified files. This prevents the "I already addressed that" reasoning that causes agents to skip findings they hallucinate as resolved.

**For task design:** one skill, one responsibility, one output per run. If the task requires multiple things, decompose it into multiple sequential or parallel agents — don't hand everything to one agent and hope it tracks it all.

### 10. Blame Deflection — "Pre-existing Issue"

This is one of the most reliable failure patterns in agents that have build/test verification steps.

The pattern:
1. Agent implements a change
2. Runs a build or test
3. Encounters an error that predates its changes
4. Identifies it as "pre-existing" — not caused by the changes
5. Scopes the build to work around it (runs only the main scheme, skips tests)
6. Reports success

From a real session:

> The code agent hit a typo in `UITestConveniences.swift`: `@discardableResults` instead of `@discardableResult` — a pre-existing error it didn't introduce. It correctly identified the error as pre-existing, then scoped the build to just the main app scheme to "verify my changes compile." Tests never ran. The verification was hollow.

The agent followed the letter of reasonable reasoning ("I didn't cause this") while violating the spirit of the verification step ("confirm the full build is clean"). The result was a false green.

The explicit fix added to the skill:

> Fix all compiler errors, compiler warnings, and linter errors/warnings — including pre-existing ones unrelated to your changes. "Pre-existing" is not a valid reason to leave a warning or error unfixed.

The deeper issue: the agent couldn't know which errors existed before it started because it had no baseline. Capturing a build baseline at the start of any implementation phase gives the agent a diff to work with instead of forcing it to reason about provenance.

---

## Part 3 — Dark Factories

These are systemic problems, not individual failure modes. They describe the structural conditions under which the failure modes in Part 2 occur.

### 11. AI Validating Itself

An agent that implements a change and then verifies that change is not performing a real review. It is performing a consistency check — "does my output match my intent?" That is not the same question as "is my output correct?"

From a real session, the agent's Phase 6 output:

> "Everything is in order."

Two problems were present that the agent didn't catch:
1. It had used a stored memory to justify skipping two Phase 5 steps
2. It had left pre-existing lint warnings unfixed

The agent wasn't concealing these — it genuinely didn't identify them as problems, because the criteria it was applying were its own. A fresh eye (the human reviewing the output) caught both immediately.

**The structural problem:** the same context window that wrote the code also evaluated whether the code is correct. The agent's evaluation is shaped by the same reasoning that produced the output. It will find the output satisfactory because it understands why every decision was made.

This is why solid-coder's iteration loop is stateless. Each re-review is a fresh agent with no knowledge of what the previous agent intended. It just sees the code and applies the rules.

**Design principle:** review and implementation should run in separate agents, with separate context windows. The reviewer should have no access to the implementer's reasoning — only its output.

### 12. AI Filling the Blanks

When an agent encounters a gap in its knowledge — a type it doesn't have context for, an API it hasn't seen defined, a value set it doesn't know — it doesn't stop. It fills the blank with the most plausible thing it can construct.

This behavior is a feature in conversational AI (it makes responses coherent) and a liability in code generation (it makes outputs plausible but incorrect).

The `AlloyTextStyle` example is the canonical case: the agent had never seen the type defined, knew it was a text style type, and populated it with UIKit text style names. The output compiled (it was syntactically valid), failed at build time (the members didn't exist), and looked right at a glance.

**Other forms this takes:**
- Generating method signatures for an injected protocol that don't match the actual protocol
- Referencing a module that exists in a different project or an older version of the codebase
- Producing JSON with field names from a different schema than the one being used
- Writing test assertions for behavior the code doesn't actually implement

**The pattern:** the agent produced something that exists *somewhere in its training data* but not in this specific codebase.

**The countermeasure:** give agents explicit, bounded context. Instead of "use the design system's text styles," pass the actual type definition or an explicit list of valid values. Don't let the agent infer what's available — tell it.

### 13. AI Confidence Level Means Nothing

An agent's confidence in its output has no reliable correlation with whether the output is correct.

Agents say things like:
- "I'm confident this resolves the issue"
- "This should fix it"
- "Everything is in order"
- "This is correct"

These statements are produced by the same sampling process as every other token in the output. They reflect the internal coherence of the agent's reasoning, not the accuracy of the result.

In practice, the most dangerous agent outputs are the ones delivered with high confidence and no qualification. Low-confidence outputs ("I'm not sure about this, you may want to verify") at least signal that verification is needed.

**The correlation with Section 8 (context overload):** as the complexity of a task increases, the agent's confidence tends to *increase* rather than decrease. This is because the agent is completing a large, internally consistent narrative — it all fits together, therefore it must be correct. The verification that would catch the error was either skipped, scoped down, or self-administered.

**Practical implication for skill design:** never let the agent's stated confidence substitute for a real external verification step. The only valid verification is: build passes, tests pass, output schema validates, human reviews the diff. An agent saying "everything looks good" is not a verification.

---

## Part 4 — Design Principles That Help

### 14. Single Responsibility per Skill/Agent

The same principle that applies to code applies to agents. A skill that does two things has two reasons to fail and two reasons to drift. When something goes wrong, you can't tell which of the two responsibilities caused it.

In solid-coder, the review and fix suggestion steps were initially bundled in one agent (`principle-review-fx-agent`). They were later split — `apply-principle-review-agent` (review only, in the refactor path) vs `principle-review-fx-agent` (review + fix, in the review path). The split was driven by a practical need (refactor synthesizes fixes holistically, not per-principle), but it also made each agent easier to reason about and test against examples.

### 15. Explicit Phases with Checkpoints

A skill's instructions should be structured as numbered phases with numbered steps. Each step either completes or has an explicit condition under which it is skipped. There are no implicit steps.

The checkpoint pattern:
```
- [ ] 3.1 Run build
- [ ] 3.2 If build fails → fix errors, return to 3.1
- [ ] 3.3 If build passes → continue
```

This is not just documentation style. An agent reading this structure knows exactly what the expected flow is, what "done" means, and what to do when something goes wrong. A phase-structured skill is also easier to debug — when an agent skips something it shouldn't, you can identify exactly which step was missed.

### 16. Constrained Tools per Agent

Each agent should only have access to the tools it needs. An agent that can do anything will do anything.

In solid-coder's agent definitions, tools are explicitly listed in frontmatter:
- Review agents: `Read, Glob, Grep` — no write access
- Code agents: `Read, Edit, Write, Bash, Glob, Grep` — full access
- Validation agents: `Read, Bash` — only what the script needs

When a review agent can't call `Edit`, it physically cannot modify source files, even if it reasons its way into believing it should. The constraint is enforced at the infrastructure level, not the instruction level.

### 17. External Validators over Self-Review

An agent should not be the primary reviewer of its own output. External validation — a separate agent, a script, a schema validator, a build — should be the signal that work is complete.

The hierarchy:
1. **Compiler/build** — binary pass/fail, no interpretation needed
2. **Tests** — behavioral verification against specified expectations
3. **Schema validation** — structural correctness of intermediate artifacts
4. **Separate review agent** — no shared context with the implementer
5. **Human review** — final authority

Self-review ("let me verify my changes are correct") is useful for catching obvious mistakes but structurally cannot catch the category of errors described in Part 3. An agent that validates its own output will find it satisfactory for the same reason it produced it.

The iteration loop in solid-coder's refactor pipeline embodies this: after implementation, a fresh review agent runs against the modified files. It doesn't know what was intended. It just applies the rules to what's there.

---

*Built from sessions on solid-coder (Swift SOLID principles pipeline) and Autodesk build-mobile-ios (iOS production app). All examples are from real agent runs.*
