<fix id="SUI-2" name="View Purity">

<trigger>
Methods or computed properties in a View struct perform impure operations:
data fetching, sorting/filtering, input validation, calculations, or state machine
transitions. Views must be dumb — functions of state only.
</trigger>

<strategy severity="SEVERE">
Move all impure methods to a ViewModel. The view reads from ViewModel state and
triggers ViewModel actions — it never computes, fetches, or validates.
</strategy>

<todo>
- [ ] If no ViewModel exists: create one following SUI-4 guidance (State + Actions protocols)
- [ ] Move each impure method/computed property to the ViewModel:
  - DATA_FETCH → ViewModel method called on `.onAppear` or triggered by action
  - TRANSFORM → ViewModel computed property
  - FORMAT → ViewModel computed property (unless using SwiftUI-native `Text(value, format:)`)
  - VALIDATE → ViewModel method
  - COMPUTE → ViewModel computed property
- [ ] Update the view to read the result from ViewModel state instead of computing inline
- [ ] Leave in view only: toggling simple UI state (`showSheet = true`) and `some View`-returning properties
</todo>

<suggested_fix_must_include>
- ViewModel with moved methods/computed properties
- Updated View reading from ViewModel state
- Before/after showing impure logic removed from View
</suggested_fix_must_include>

</fix>
