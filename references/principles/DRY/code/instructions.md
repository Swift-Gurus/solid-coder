---
name: dry-code
type: code
---

# DRY Coding Instructions

<rule id="DRY-1" name="Search Before Creating">
Before creating anything — type, function, private helper, view builder, computed property, extension, or inline expression — search the codebase first.

Run both phases:

**Phase A — Frontmatter search:**
- Generate keywords and 3 domain-aware synonyms per keyword from the name and responsibility of what you are about to create.
- Run: `mcp__plugin_solid-coder_pipeline__search_codebase` with `sources_dir` and `synonyms`.

**Phase B — Name-based search (always runs):**
- Search for extensions on types you are using — convenience wrappers are commonly missed.
- Search shared/common directories and design system modules for equivalent components.
- Use Grep and Glob across filenames and file contents.

**Classify each match:**
- EXACT — same responsibility, compatible interface → reuse directly, do not create.
- EXTENSIBLE — similar responsibility, could be extended → extend it, do not duplicate.
- PARTIAL — overlapping keywords but genuinely different purpose → not a reuse miss.

**Before suggesting where to put shared code, verify reachability:**
Classification tells you *what* exists. Reachability tells you *where* the abstraction can actually live.

For each EXACT or EXTENSIBLE match, ask:

1. **Same module/target?** → reuse or extend in place. No further check needed.

2. **Different module/package?** → pick based on the semantic relationship:
   - (a) **Add the import/dependency** — correct if the existing module is a genuine shared utilities package (e.g., a dedicated test-helpers framework). Name it explicitly: "move to X, which requires adding import Y."
   - (b) **Extract to the nearest accessible common ancestor in the current module** — correct if the other module is a peer feature package and a dependency would create horizontal feature coupling.
   - (c) **Find or create a shared module** — correct when no accessible common ancestor exists AND the abstraction is generic enough to serve multiple modules.
     First, look for an existing module in the project that already collects shared or utility code of the same kind. If one exists and fits → move the abstraction there. Only if nothing suitable exists → propose a new module following the project's own naming and structural conventions.

3. **Different class hierarchy branch (sibling, not ancestor)?** → do NOT suggest moving to the sibling class. Identify the deepest common base class that is accessible in the current module and suggest extracting there. If no accessible common base exists, apply option (c) above.

Never suggest moving code to a type in a different package without explicitly stating whether it requires a dependency change or a new module.
</rule>

<rule id="DRY-2" name="No Logic Duplication">
Before writing any function or method, identify its logical sequence — what operations does it perform, in what order?
- Check other methods in the same module for the same logical sequence (same control flow, same operation ordering, same algorithm — even with different variable names or types).
- IDENTICAL or STRUCTURAL match found → extract a shared abstraction, do not copy-paste.
</rule>

<rule id="DRY-3" name="Extract Generic Patterns">
Before inlining any of the following, ask: could another part of the codebase need this same thing?
- Behavioral patterns — retry, queue, cache, observe, poll, transform pipeline, validation chain.
- UI composition patterns — recurring view structures, repeated styling and layout combinations, interactive elements with shared behavior.
- Object creation patterns — similar initialization sequences, builder logic, factory patterns repeated across types.

If YES → extract it as a standalone abstraction before writing it inline.
If NO (inherently domain-specific) → proceed.
</rule>

<exceptions>
- Intentionally specialized — same shape but genuinely different domain semantics (e.g., two validation functions with similar structure but different business rules).
- Configuration / constants — repeated literal values that are intentionally independent (changing one should NOT change the other).
- Protocol default implementations — providing defaults for convenience is not duplication even if the body resembles another conformer.
</exceptions>
