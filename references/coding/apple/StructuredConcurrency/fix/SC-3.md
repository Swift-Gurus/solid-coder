<fix id="SC-3" name="Concurrency Safety Bypasses">

<trigger>
`@unchecked Sendable` or `nonisolated(unsafe)` used to silence the compiler
without fixing the underlying concurrency problem.
</trigger>

<strategy severity="SEVERE">
Remove the bypass and fix the root cause. Never move the bypass elsewhere.
</strategy>

<todo>
**For `@unchecked Sendable` on a type you own:**
- [ ] No reference/identity requirement → convert to `struct` (synthesised `Sendable` when all stored properties are `Sendable`)
- [ ] Mutable state with concurrent access → use `actor` — isolation is compiler-verified
- [ ] Third-party non-`Sendable` type you don't own:
  - iOS 16+ / macOS 13+ → wrap in `OSAllocatedUnfairLock<T>`
  - Older deployment → check for an existing project lock abstraction, or create `Lock<T>` backed by `os_unfair_lock`
- [ ] `@unchecked Sendable` is ONLY acceptable on a type that IS itself a synchronisation primitive (e.g. your own `Lock<T>`) — one-time project-level utility, not a per-use-case escape hatch

**For `nonisolated(unsafe)`:**
- [ ] Restructure to avoid the boundary crossing
- [ ] Or use actor isolation for the affected property

</todo>

<suggested_fix_must_include>
- Before/after showing the bypass removed
- Replacement with struct, actor, or lock wrapper
- Updated property/type declarations
</suggested_fix_must_include>

</fix>
