<fix id="SC-1" name="Concurrency Model Mixing">

<trigger>
A type uses more than one concurrency model — `async/await` mixed with GCD
(`DispatchQueue.async`) or completion handlers.
</trigger>

<strategy severity="SEVERE">
Migrate all code in the type to async/await. Do not keep mixed models.
</strategy>

<todo>
- [ ] Replace `DispatchQueue.main.async { }` with `await MainActor.run { }` or mark the method `@MainActor`
- [ ] Replace `DispatchQueue.global().async { }` — question why background dispatch is needed. Usually the function should be `async` and the caller should `await` it. Only use `Task { }` when fire-and-forget is the actual intent.
- [ ] Replace completion handler patterns with async/await return values
- [ ] Remove all GCD imports if no GCD usage remains after migration
- [ ] Ensure callers are updated to `await` the migrated methods
</todo>

<suggested_fix_must_include>
- Before/after of each replaced DispatchQueue call
- Updated function signatures (sync → async, completion handler → return value)
- Updated call sites showing `await` usage
</suggested_fix_must_include>

</fix>
