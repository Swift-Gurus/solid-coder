<fix id="SUI-4" name="ViewModel Injection">

<trigger>
A View holds a concrete ViewModel class type. The dependency is sealed —
the view cannot be used with a different implementation.
</trigger>

<strategy severity="SEVERE">
Extract State + Actions protocols from the ViewModel. Inject via the correct
style for whether the protocol extends `Observable`.
</strategy>

<todo>
- [ ] Extract a **State protocol** (readable properties the view observes)
- [ ] Extract an **Actions protocol** (methods the view triggers)
- [ ] Make the existing ViewModel conform to both protocols

**If the State protocol extends `Observable` (observation-tracked properties):**
- [ ] Add a generic constraint to the view: `struct MyView<VM: MyState & MyActions>: View`
- [ ] Use `@State` only if the view owns the VM lifecycle; use plain `let`/`var` if injected
- [ ] For two-way bindings: use `@Bindable var bindable = vm` inside `body` to get the `$` projection — do NOT use manual `Binding(get:set:)`
- [ ] State protocol properties that need binding must be declared `{ get set }`

**If the Actions protocol does NOT extend `Observable` (no observation needed):**
- [ ] Use a plain protocol-typed property (`let actions: MyActions`) — no generic needed
</todo>

<suggested_fix_must_include>
- State protocol and Actions protocol definitions
- ViewModel conformance to both
- Updated View with generic constraint (or plain property for non-observable)
- `@Bindable` usage for two-way binding (if applicable)
- Before/after showing concrete type replaced with protocol interface
</suggested_fix_must_include>

</fix>
