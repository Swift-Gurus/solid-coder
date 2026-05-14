<fix id="SC-2" name="Unstructured Task Lifecycle">

<trigger>
`Task { }` or `Task.detached { }` created without storing the handle or providing
a cancellation path. Orphaned or leaked tasks.
</trigger>

<strategy severity="SEVERE">
Store every Task handle in a property and cancel it in `deinit` or a dedicated cleanup method.
</strategy>

<todo>
- [ ] For each orphaned task (`Task { }` with no stored handle):
  - Check if the project has an existing task management utility — use it if available
  - Otherwise store the handle: `private var loadTask: Task<Void, Never>?`
  - Assign before launching: `loadTask = Task { ... }`
- [ ] For each stored handle with no cancellation:
  - Add `loadTask?.cancel()` in `deinit` or a dedicated cleanup/teardown method
- [ ] Replace `Task.detached { }` with `Task { }` when actor context inheritance is correct — only use `detached` when you specifically need to escape actor context
- [ ] Add `try Task.checkCancellation()` inside any long-running loops in tasks
</todo>

<suggested_fix_must_include>
- Task handle property declaration
- Updated task launch storing the handle
- `deinit` or cleanup method with cancellation
- Before/after showing the lifecycle management
</suggested_fix_must_include>

</fix>
