<fix id="SUI-3" name="Modifier Chain Length">

<trigger>
A child view inside a `@ViewBuilder` closure has 2+ chained modifiers. Applies
only to nested views inside closures — NOT to the outermost view returned by
`body` or a computed property.
</trigger>

<strategy severity="SEVERE">
Extract each over-modified nested view into a named `private var` computed property.
</strategy>

<todo>
- [ ] Identify each child view inside a `@ViewBuilder` closure with 2+ modifiers
- [ ] For each: extract it to a named `private var` (name describes what it represents, not its modifiers)
- [ ] Replace the inline expression in the closure with the named variable reference
- [ ] Modifiers on the outermost returned view do NOT need extraction — only nested children
</todo>

<suggested_fix_must_include>
- Named `private var` computed property containing the extracted view + modifiers
- Updated closure body showing the variable reference replacing the inline expression
- Before/after
</suggested_fix_must_include>

</fix>
