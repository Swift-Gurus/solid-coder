<fix id="SC-5" name="Sync-to-Async Blocking">

<trigger>
Synchronous code blocks waiting for async results using `DispatchSemaphore`,
`DispatchGroup.wait()`, `RunLoop.current.run`, or inappropriate
`withCheckedContinuation` where a native async API exists.
</trigger>

<strategy severity="SEVERE">
Make the caller async instead of blocking. Remove all blocking wait mechanisms.
</strategy>

<todo>
**For `DispatchSemaphore` / `DispatchGroup.wait()` blocking:**
- [ ] Make the function `async` and replace the blocking wait with direct `await`
- [ ] Update all call sites to `await` the function

**For `withCheckedContinuation` / `withUnsafeContinuation`:**
- [ ] Check if a native `async` API exists in the SDK for what is being wrapped
  - If YES → use the native async API directly, remove the continuation
  - If NO (legacy callback API with no async version) → keep the continuation but document the reason. Verify every code path resumes exactly once.

</todo>

<suggested_fix_must_include>
- Before/after showing blocking mechanism removed
- Updated function signature (sync → async)
- Updated call sites with `await`
- Note explaining why continuation was kept (if applicable)
</suggested_fix_must_include>

</fix>
