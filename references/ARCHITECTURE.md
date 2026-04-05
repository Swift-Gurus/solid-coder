# Solid-Coder Architecture

## Principle Categories & Tiers

Principles are organized into tiers that control activation and cross-checking behavior.

### Tiers

| Tier | Always applies? | Examples | Cross-checked BY |
|------|----------------|----------|------------------|
| **core** | Yes | SRP, OCP, LSP, ISP, DIP | Other core principles |
| **practice** | Yes | DRY, Bugs, functions/smells | Core + other practices |
| **framework** | Only when detected | SwiftUI, TCA | Core + practice (one-way up) |

### Cross-Check Direction

Cross-checking is **directional** — lower tiers never check higher tiers, but higher tiers always get checked by lower tiers. Core (SOLID) is the foundation; everything must satisfy it.

```
core × core           → full cross-check (bidirectional)
core × practice       → light cross-check (bidirectional)
core ← framework      → core checks framework fixes (one-way UP)
practice ← framework  → practice checks framework fixes (one-way UP)
framework × framework → no cross-check
```

**Rule:** Any fix that moves, creates, or restructures code gets verified against all core principle metrics.

### Activation

Each principle declares how it activates in its `rule.md` frontmatter:

```yaml
# Always active (core, practice)
---
activation: always
cross_check_tier: core
---
```

```yaml
# Conditional on imports (framework)
---
activation:
  imports: ["ComposableArchitecture"]
cross_check_tier: framework
---
```

The `prepare-review-input` phase detects imports from source files and writes them to `review-input.json` as `detected_imports`. The orchestrator filters principles at discovery time.

---

## Directory Structure

```
references/
├── SRP/              activation: always,  tier: core
├── OCP/              activation: always,  tier: core
├── LSP/              activation: always,  tier: core
├── ISP/              activation: always,  tier: core
├── DIP/              activation: always,  tier: core      (future)
├── DRY/              activation: always,  tier: practice
├── Bugs/             activation: always,  tier: practice
├── functions/        activation: always,  tier: practice  (future)
├── SwiftUI/          activation: import,  tier: framework (future)
├── TCA/              activation: import,  tier: framework (future)
├── design_patterns/  (shared knowledge, not a reviewable principle)
```

Each principle follows the same structure:

```
references/{PRINCIPLE}/
  rule.md                    — metrics, severity bands, frontmatter (activation, tier, required_patterns)
  review/
    instructions.md          — how to detect violations
    output.schema.json       — structured review output
  fix/
    instructions.md          — how to generate fix suggestions
    output.schema.json       — structured fix output
  refactoring.md             — patterns and code examples
```

---

## Severity Bands

All principles use the same three-level severity vocabulary:

| Level | Meaning |
|-------|---------|
| **COMPLIANT** | No violations detected |
| **MINOR** | Low-risk finding, no refactoring needed |
| **SEVERE** | Structural violation, refactoring required |

---

## Pipeline Overview

```
1. Prepare Input
   - Parse target (branch/changes/folder/file)
   - Read source files
   - Detect imports → detected_imports
   - Identify units (class, struct, enum, extension)
   - Write review-input.json

2. Discover Principles
   - Glob for references/**/review/instructions.md
   - Read each rule.md frontmatter for activation + tier
   - Filter: always → include; imports → include if detected
   - Build active principle list

3. Parallel Review
   - Launch one review agent per active principle
   - Each agent reads its own rule.md + review/instructions.md
   - Produces review-output.json per principle

4. Validate Findings
   - Filter findings to changed ranges only
   - Reorganize by file (by-file/*.output.json)
   - Schema-validate agent outputs when plugin-root provided

5. Synthesize Fixes (two-pass)
   - See "Two-Pass Synthesizer" section below

6. Implement
   - One agent per file, follows the plan
   - Edit tool for code changes

7. Re-review (iteration loop)
   - Re-run on changed files only
   - Max iterations configurable
```

---

## Two-Pass Synthesizer

The synthesizer generates a unified fix plan per file. It operates in two passes to separate creative work (generating fixes) from verification work (cross-checking).

### Pass 1: Draft Fix Actions

For each file with non-COMPLIANT findings:

1. Group findings by unit (class/struct/enum)
2. For each unit, for each violated principle:
   - Load that principle's fix/instructions.md + refactoring.md
   - Generate a draft fix action using ONLY that principle's knowledge
   - Record which findings the action resolves
3. Output: list of draft actions, each tagged with its primary principle

Each draft action is focused — it solves one principle's violations without worrying about others.

### Pass 2: Verify & Patch

Cross-checks reuse each principle's existing `rule.md` metrics and `fix/instructions.md` patterns — no separate recipe files needed. This scales linearly: adding a new principle requires only its own rule.md and fix/instructions.md.

For each draft action:

1. Determine which principles need to cross-check this action based on tier rules:
   - Action from core principle → check against all other active core principles
   - Action from practice principle → check against all core + other practices
   - Action from framework principle → check against all core + all practice
2. For each cross-checking principle, apply its `rule.md` metrics to the proposed code:
   - SRP: count cohesion groups and verbs in new/modified types
   - OCP: count sealed variation points in new/modified types
   - LSP: check for type checks, contract violations, empty methods in new protocols
3. If a check fails, apply that principle's `fix/instructions.md` patterns to patch:
   - SRP fail → split the type further along cohesion boundaries
   - OCP fail → wrap concrete deps behind protocols, inject via init
   - LSP fail → split protocol so conformers only implement what they use
4. Re-verify after patching. If still failing → mark as `unresolved` with reason
5. Record cross-check results in the action

**Unresolved findings are not failures.** The synthesizer's job is to not make things worse and be honest about what it couldn't fix. Unresolved findings surface as new findings in the next iteration's re-review, where they get their own focused fix with fresh context. This is by design — the iteration loop (Phase 8 of refactor) is the safety net. The synthesizer does not attempt to recursively fix its own fixes.

### Pass 3: Merge & Order

1. If multiple actions touch the same unit, look for synergies (e.g., SRP extraction + OCP protocol injection can merge into one action)
2. Apply dependency ordering (action A creates type that action B modifies → B depends on A)
3. Order by: dependency graph first, then severity (SEVERE → MINOR)
4. Verify completeness: every finding in exactly one action's `resolves` or in `unresolved`
