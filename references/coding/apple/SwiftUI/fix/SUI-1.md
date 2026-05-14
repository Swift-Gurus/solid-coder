<fix id="SUI-1" name="Body Complexity">

<trigger>
`body` or a view-returning computed property exceeds nesting depth 2 or has 5+
distinct view expressions. Complexity in helper `var`s still counts — each
view-returning property is measured independently.
</trigger>

<strategy severity="SEVERE">
Extract coherent sections of `body` into named subviews. Each extracted subview
should represent a meaningful UI component with clearly defined inputs.
</strategy>

<todo>
- [ ] Identify coherent sections in `body` that exceed the depth/expression threshold
- [ ] For each section: name a new subview struct (`private struct`, or separate file if reused), define what state it needs as properties
- [ ] Extract the section into the new subview, passing only the data it needs
- [ ] Replace the inline section in `body` with the named subview call
- [ ] Verify each view-returning property is now independently under threshold
</todo>

<suggested_fix_must_include>
- New subview struct(s) with their properties and `body`
- Modified parent view with extracted subviews replacing inline sections
- Before/after of `body` structure showing depth reduction
</suggested_fix_must_include>

</fix>
