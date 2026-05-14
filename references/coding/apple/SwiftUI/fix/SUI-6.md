<fix id="SUI-6" name="Preview Coverage">

<trigger>
A file-scope View struct has no `#Preview` block or `PreviewProvider` anywhere in
the codebase — neither in the same file nor a dedicated preview file.
</trigger>

<strategy severity="SEVERE">
Create a dedicated preview file showing the view's key states.
</strategy>

<todo>
- [ ] Create a dedicated preview file in a `Previews/` folder at the component root
- [ ] Name it `{ViewName}Previews.swift`
- [ ] Add `#Preview` blocks showing the view's key states:
  - Default/empty state
  - Populated/loaded state
  - Edge cases (long text, error state, disabled state)
- [ ] Use sample data only — no real network calls, no real dependencies
- [ ] Do NOT add a `#Preview` in the production file if a dedicated preview file is more appropriate
</todo>

<suggested_fix_must_include>
- Preview file with `#Preview` blocks for each key state
- Sample data showing realistic content
</suggested_fix_must_include>

</fix>
