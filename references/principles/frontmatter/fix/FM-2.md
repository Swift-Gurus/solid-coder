<fix id="FM-2" name="solid-name does not match the declared type">

<trigger>
A frontmatter block's `solid-name` does not exactly match the name of the type
declared immediately below it.
</trigger>

<strategy severity="SEVERE">
Set `solid-name` to the exact declared type name — no abbreviation, no old name
left over from a rename, no unrelated string. Change nothing else in the block.
</strategy>

<diagnosis>
For each flagged type, compare the frontmatter's `solid-name` value against the
actual declared type/class/struct/protocol/enum name in the code below it.
</diagnosis>

<todo>
- [ ] List each type with a solid-name mismatch from the findings
- [ ] For each: set solid-name to the exact declared type name
- [ ] Verify: every solid-name in the file matches its declaration
</todo>

<suggested_fix_must_include>
- Old solid-name value → corrected value, per flagged type
</suggested_fix_must_include>

</fix>
