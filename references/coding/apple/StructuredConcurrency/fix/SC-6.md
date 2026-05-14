<fix id="SC-6" name="Raw Duration API">

<trigger>
`Task.sleep(nanoseconds:)` or raw integer literals used for time durations
(nanoseconds, milliseconds) instead of the Swift `Duration` API.
</trigger>

<strategy severity="SEVERE">
Replace all raw time values with the `Duration` API.
</strategy>

<todo>
- [ ] Replace `Task.sleep(nanoseconds: N)` with `Task.sleep(for: .seconds(N))` or the appropriate unit (`.milliseconds()`, `.minutes()`)
- [ ] Replace raw nanosecond/millisecond integer literals used as time durations with `.seconds()`, `.milliseconds()`, `.minutes()` wherever the value represents a time duration:
  - Timeouts
  - Delays
  - Polling intervals
  - Any time duration parameter
</todo>

<suggested_fix_must_include>
- Before/after of each replaced raw time value
- Correct `Duration` unit selection (seconds, milliseconds, minutes)
</suggested_fix_must_include>

</fix>
