<fix id="SC-4" name="Sequential Awaits on Independent Calls">

<trigger>
Two or more `await` calls in the same scope that are independent — the second
does not use the result of the first. Running sequentially wastes time.
</trigger>

<strategy severity="SEVERE">
Make independent awaits concurrent using `async let` (for 2–3 calls) or
`TaskGroup` (for dynamic counts).
</strategy>

<todo>
**For 2–3 independent calls:**
- [ ] Replace sequential `let a = await foo(); let b = await bar()` with:
  ```swift
  async let a = foo()
  async let b = bar()
  let (result1, result2) = await (a, b)
  ```

**For dynamic counts:**
- [ ] Replace with `withTaskGroup` or `withThrowingTaskGroup`:
  ```swift
  await withTaskGroup(of: ResultType.self) { group in
      for item in items {
          group.addTask { await process(item) }
      }
      for await result in group { collect(result) }
  }
  ```
</todo>

<suggested_fix_must_include>
- Before/after showing sequential → concurrent awaits
- `async let` binding for 2–3 calls
- TaskGroup pattern for dynamic counts
</suggested_fix_must_include>

</fix>
